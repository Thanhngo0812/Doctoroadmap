import { describe, expect, it, vi } from 'vitest';
import { apiFetch, apiJson, fetchHealth, readSse, setCsrfToken } from './api';

describe('apiFetch', () => {
  it('sends cookies on reads and attaches the in-memory CSRF token on writes only', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{}'));
    setCsrfToken('abc/123');

    await apiFetch('/api/v1/health');
    await apiFetch('/api/v1/demo', { method: 'post' });

    expect(fetchSpy.mock.calls[0]?.[1]).toMatchObject({ credentials: 'include', method: 'GET' });
    expect(new Headers(fetchSpy.mock.calls[0]?.[1]?.headers).has('X-CSRF-Token')).toBe(false);
    expect(new Headers(fetchSpy.mock.calls[1]?.[1]?.headers).get('X-CSRF-Token')).toBe('abc/123');
    setCsrfToken(null);
    await apiFetch('/api/v1/demo', { method: 'post' });
    expect(new Headers(fetchSpy.mock.calls[2]?.[1]?.headers).has('X-CSRF-Token')).toBe(false);
    fetchSpy.mockRestore();
  });

  it.each([
    ['unauthenticated', 'Phiên làm việc đã hết hạn. Hãy đăng nhập lại.'],
    ['conflict', 'Dữ liệu vừa thay đổi. Hãy tải lại rồi thử lại.'],
    ['validation', 'Thông tin chưa hợp lệ. Hãy kiểm tra lại rồi thử lại.'],
    ['owns_shared_courses', 'Hãy chuyển quyền sở hữu khoá học trước khi xoá tài khoản.'],
  ])('maps %s to a stable Vietnamese message', async (code, message) => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(
      JSON.stringify({ error: { code } }), { status: 400 },
    ));
    await expect(apiJson('/api/v1/action')).rejects.toMatchObject({ code, message });
  });

  it('maps structured server errors to Vietnamese without exposing raw server text', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(
      JSON.stringify({ error: { code: 'file_too_large', message: 'Raw internal text' } }),
      { status: 413, headers: { 'content-type': 'application/json' } },
    ));

    await expect(apiJson('/api/v1/upload')).rejects.toMatchObject({
      code: 'file_too_large',
      message: 'Tệp lớn hơn 10 MB. Hãy tách tài liệu theo chương rồi tải từng phần.',
    });
  });

  it('keeps a valid degraded health payload when the API uses HTTP 503 for database downtime', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(
      JSON.stringify({ status: 'degraded', version: '0.1.0', db: 'down' }),
      { status: 503, headers: { 'content-type': 'application/json' } },
    ));

    await expect(fetchHealth()).resolves.toEqual({ status: 'degraded', version: '0.1.0', db: 'down' });
  });
});

describe('readSse', () => {
  it('parses events across CRLF boundaries and a split multibyte Vietnamese character', async () => {
    const encoder = new TextEncoder();
    const bytes = encoder.encode('event: token\r\ndata: Học\n\ndata: tiến\n\n');
    const split = bytes.findIndex((byte, index) => byte === 0xE1 && bytes[index + 1] === 0xBA);
    const pieces = [bytes.slice(0, split + 1), bytes.slice(split + 1, split + 2), bytes.slice(split + 2)];
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        pieces.forEach((piece) => controller.enqueue(piece));
        controller.close();
      },
    });
    const events: unknown[] = [];

    await readSse(new Response(stream), (event) => events.push(event));

    expect(events).toEqual([{ event: 'token', data: 'Học' }, { event: 'message', data: 'tiến' }]);
  });

  it('joins multiline data and ignores comments', async () => {
    const events: unknown[] = [];
    await readSse(new Response(': ping\nevent: note\nid: 3\ndata: dòng một\ndata:dòng hai\nretry: 2500\n\n'), (event) => events.push(event));
    expect(events).toEqual([{ event: 'note', data: 'dòng một\ndòng hai', id: '3', retry: 2500 }]);
  });

  it('keeps multiline data together when a CRLF pair is split between chunks', async () => {
    const chunks = ['data: đầu\r', '\ndata: cuối\r\n\r', '\n'];
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        chunks.forEach((chunk) => controller.enqueue(new TextEncoder().encode(chunk)));
        controller.close();
      },
    });
    const events: unknown[] = [];

    await readSse(new Response(stream), (event) => events.push(event));

    expect(events).toEqual([{ event: 'message', data: 'đầu\ncuối' }]);
  });

  it('drops an event that is not terminated by a blank line at EOF', async () => {
    const events: unknown[] = [];
    await readSse(new Response('data: incomplete'), (event) => events.push(event));
    expect(events).toEqual([]);
  });

  it('keeps the last event ID across messages', async () => {
    const events: unknown[] = [];
    await readSse(new Response('id: 42\ndata: one\n\ndata: two\n\n'), (event) => events.push(event));
    expect(events).toEqual([
      { event: 'message', data: 'one', id: '42' },
      { event: 'message', data: 'two', id: '42' },
    ]);
  });

  it('preserves structured API errors from a failed SSE response', async () => {
    const response = new Response(JSON.stringify({
      error: { code: 'rate_limited', retry_after: 30, ref: 'req-123' },
    }), { status: 429 });
    await expect(readSse(response, () => undefined)).rejects.toMatchObject({
      code: 'rate_limited', retryAfter: 30, ref: 'req-123',
      message: 'Bạn thử nhiều lần quá. Thử lại sau 30.',
    });
  });

  it('cancels the stream when an event callback throws', async () => {
    let cancelled = false;
    const stream = new ReadableStream<Uint8Array>({
      start(controller) { controller.enqueue(new TextEncoder().encode('data: stop\n\n')); },
      cancel() { cancelled = true; },
    });
    await expect(readSse(new Response(stream), () => { throw new Error('stop'); }))
      .rejects.toThrow('stop');
    expect(cancelled).toBe(true);
  });

  it('cancels an already-aborted stream and releases its reader', async () => {
    let cancelled = false;
    const stream = new ReadableStream<Uint8Array>({ cancel() { cancelled = true; } });
    const controller = new AbortController();
    controller.abort();
    await expect(readSse(new Response(stream), () => undefined, controller.signal))
      .rejects.toMatchObject({ name: 'AbortError' });
    expect(cancelled).toBe(true);
    await expect(stream.getReader().cancel()).resolves.toBeUndefined();
  });
});
