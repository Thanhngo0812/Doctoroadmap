import { afterEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen } from '@testing-library/react';
import TaskWait from './TaskWait';

afterEach(() => { cleanup(); vi.useRealTimers(); });

describe('TaskWait', () => {
  it('waits at least 400ms, then exposes an animated WebP with a GIF fallback and status text', async () => {
    vi.useFakeTimers();
    Object.defineProperty(window, 'matchMedia', {
      configurable: true,
      value: vi.fn().mockReturnValue({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }),
    });
    const { container } = render(<TaskWait message="Đang soạn bài giảng" />);

    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    await act(async () => { await vi.advanceTimersByTimeAsync(399); });
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    await act(async () => { await vi.advanceTimersByTimeAsync(1); });

    expect(screen.getByRole('status')).toHaveTextContent('Đang soạn bài giảng');
    expect(container.querySelector('source[type="image/webp"]')).toHaveAttribute('srcset', '/assets/wayfinder-wait.webp');
    expect(container.querySelector('img')).toHaveAttribute('src', '/assets/wayfinder-wait.gif');
  });

  it('uses only the static PNG when reduced motion is requested', async () => {
    vi.useFakeTimers();
    Object.defineProperty(window, 'matchMedia', {
      configurable: true,
      value: vi.fn().mockReturnValue({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() }),
    });
    const { container } = render(<TaskWait message="Đang tạo quiz" />);
    await act(async () => { await vi.advanceTimersByTimeAsync(400); });

    expect(screen.getByRole('status')).toHaveTextContent('Đang tạo quiz');
    expect(container.querySelector('source')).toBeNull();
    expect(container.querySelector('img')).toHaveAttribute('src', '/assets/wayfinder-wait.png');
    expect(container.innerHTML).not.toMatch(/wayfinder-wait\.(webp|gif)/);
  });
});
