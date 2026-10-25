import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import SourceViewer from './SourceViewer';

beforeEach(() => {
  Object.defineProperty(HTMLDialogElement.prototype, 'showModal', { configurable: true, value: function () { this.open = true; } });
  Object.defineProperty(HTMLDialogElement.prototype, 'close', { configurable: true, value: function () { this.open = false; } });
  Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: vi.fn(() => 'blob:w08-page') });
  Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: vi.fn() });
  vi.stubGlobal('fetch', vi.fn(async () => new Response(new Uint8Array([1]), { headers: { 'content-type': 'image/webp' } })));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

it('restores focus to the matching citation even if streaming replaces the original button', async () => {
  function Reader({ version }: { version: number }) {
    const [open, setOpen] = useState(false);
    return <><button key={version} type="button" aria-label="Nguồn S1, trang 1" onClick={() => setOpen(true)}>[S1]</button>
      {open && <SourceViewer courseId="c" initialPage={1} pageCount={3} onClose={() => setOpen(false)} />}</>;
  }
  const { rerender } = render(<Reader version={1} />);
  const original = screen.getByRole('button', { name: 'Nguồn S1, trang 1' });
  await userEvent.click(original);
  await screen.findByRole('img', { name: 'Trang 1 của tài liệu' });
  rerender(<Reader version={2} />);
  expect(original.isConnected).toBe(false);
  await userEvent.click(screen.getByRole('button', { name: 'Đóng' }));
  expect(screen.getByRole('button', { name: 'Nguồn S1, trang 1' })).toHaveFocus();
});

it('requests the actual next/previous page and keeps boundary controls disabled', async () => {
  render(<SourceViewer courseId="c" initialPage={1} pageCount={2} onClose={() => undefined} />);
  expect(screen.getByRole('button', { name: 'Trang trước' })).toBeDisabled();
  await userEvent.click(screen.getByRole('button', { name: 'Trang sau' }));
  expect(await screen.findByRole('img', { name: 'Trang 2 của tài liệu' })).toBeInTheDocument();
  expect(fetch).toHaveBeenCalledWith('/api/v1/courses/c/source/pages/2', expect.anything());
  expect(screen.getByRole('button', { name: 'Trang sau' })).toBeDisabled();
  expect(screen.getByRole('link', { name: 'Mở cả tệp' })).toHaveAttribute('href', '/api/v1/courses/c/source');
});

it('never relabels the previous image as a new page while the new request is pending', async () => {
  let finish!: (response: Response) => void;
  vi.mocked(fetch).mockImplementation(async input => String(input).endsWith('/2')
    ? new Promise<Response>(resolve => { finish = resolve; }) : new Response(new Uint8Array([1])));
  render(<SourceViewer courseId="c" initialPage={1} pageCount={2} onClose={() => undefined} />);
  const previous = await screen.findByRole('img', { name: 'Trang 1 của tài liệu' });
  await userEvent.click(screen.getByRole('button', { name: 'Trang sau' }));
  expect(previous).toHaveAttribute('alt', 'Trang 1 của tài liệu');
  expect(screen.queryByRole('img', { name: 'Trang 2 của tài liệu' })).not.toBeInTheDocument();
  await act(async () => finish(new Response(new Uint8Array([2]))));
  expect(await screen.findByRole('img', { name: 'Trang 2 của tài liệu' })).toBeInTheDocument();
});
