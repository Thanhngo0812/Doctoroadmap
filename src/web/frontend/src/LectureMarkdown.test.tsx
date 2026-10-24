import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import LectureMarkdown from './LectureMarkdown';

describe('lecture-3 safe Markdown', () => {
  it('renders inline/block LaTeX and makes only registered source labels actionable', async () => {
    const onSource = vi.fn();
    const { container } = render(<LectureMarkdown
      text={'### Một ví dụ\n\nVới $x^2$, đọc [S1] và [S999].\n\n$$\n\\frac{1}{2}\n$$\n\n`[S1]`'}
      sources={[{ label: 'S1', chunk_id: 'chunk-a', page: 37, section_path: ['Ví dụ'] }]} onSource={onSource} />);
    expect(container.querySelectorAll('.katex')).toHaveLength(2);
    expect(container.querySelector('.katex-display')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Một ví dụ' })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Nguồn S1, trang 37' })).toHaveLength(1);
    await userEvent.click(screen.getByRole('button', { name: 'Nguồn S1, trang 37' }));
    expect(onSource).toHaveBeenCalledWith(37);
    expect(screen.getByText(/\[S999\]/)).toBeInTheDocument();
    expect(container.querySelector('code')?.textContent).toBe('[S1]');
  });

  it('does not execute raw HTML, load external images, or allow dangerous links/LaTeX HTML', () => {
    const { container } = render(<LectureMarkdown text={'<script>window.pwned=true</script>\n\n<img src="https://evil.example/a" onerror="alert(1)">\n\n![image](https://evil.example/b)\n\n[bad](javascript:alert%281%29)\n\n$\\href{javascript:alert(1)}{bad}$\n\n$\\htmlClass{injected}{bad}$'} />);
    expect(container.querySelector('script,img,.injected')).toBeNull();
    for (const anchor of container.querySelectorAll('a')) {
      expect(anchor.getAttribute('href') ?? '').not.toMatch(/javascript:|data:|vbscript:/i);
    }
  });
});
