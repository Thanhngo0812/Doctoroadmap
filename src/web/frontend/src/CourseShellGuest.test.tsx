import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { CourseShell } from './Courses';

vi.mock('./Auth', () => ({ useAuth: () => ({ status: 'guest', account: null }) }));
afterEach(cleanup);

it('shows a guest login action that preserves the invite instead of an empty account menu', () => {
  render(<MemoryRouter initialEntries={['/join/test-only-token']}><CourseShell theme="light" onToggleTheme={() => {}}>Preview</CourseShell></MemoryRouter>);
  const header = screen.getByRole('banner');
  expect(header.querySelector('.account-menu')).toBeNull();
  expect(within(header).getByRole('link', { name: 'Đăng nhập để tham gia' })).toHaveAttribute('href', '/dang-nhap?next=%2Fjoin%2Ftest-only-token');
});
