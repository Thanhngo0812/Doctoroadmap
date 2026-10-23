import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useLocation } from 'react-router-dom';
import App from './App';

const invite = '/join/disposable-w11-repro-token';
const account = { id: 'w11-repro-learner', email: 'w11-repro@example.invalid', display_name: 'W11 Repro Learner', role: 'user', email_verified: false };
const identity = { account, csrf_token: 'w11-repro-csrf' };
const password = 'W11 reproducible fake passphrase!';
type Mode = 'login' | 'register';
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });

function mockHttp() {
  let authenticated = false;
  const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url === '/api/v1/me') return authenticated ? json(identity) : json({ error: { code: 'unauthenticated' } }, 401);
    if (url === '/api/v1/auth/login' && init?.method === 'POST') {
      authenticated = true;
      return json(identity);
    }
    if (url === '/api/v1/auth/register' && init?.method === 'POST') {
      authenticated = true;
      return json({ message: 'Registration accepted.' });
    }
    if (url === `/api/v1${invite}`) return json({ course_id: 'w11-repro-course', title: 'W11 invitation destination', owner: { display_name: 'Repro Owner' }, module_count: 2, concept_count: 4 });
    if (url === '/api/v1/courses') return json({ owned: [], joined: [], samples: [] });
    throw new Error(`Unexpected mocked request: ${init?.method ?? 'GET'} ${url}`);
  });
  vi.stubGlobal('fetch', fetcher);
  return fetcher;
}

function renderInvite() {
  function Location() {
    const location = useLocation();
    return <output data-testid="repro-location">{location.pathname}{location.search}</output>;
  }
  render(<MemoryRouter initialEntries={[invite]}><App /><Location /></MemoryRouter>);
}

async function enterAuth(mode: Mode, user: ReturnType<typeof userEvent.setup>) {
  await screen.findByRole('heading', { name: 'W11 invitation destination' });
  const actions = document.querySelector('.join-auth-actions') as HTMLElement;
  await user.click(within(actions).getByRole('link', { name: mode === 'login' ? 'Đăng nhập' : 'Đăng ký', exact: true }));
  expect(screen.getByTestId('repro-location')).toHaveTextContent(`next=${encodeURIComponent(invite)}`);
}

async function authenticate(mode: Mode, user: ReturnType<typeof userEvent.setup>) {
  if (mode === 'register') await user.type(screen.getByLabelText('Tên hiển thị'), account.display_name);
  await user.type(screen.getByLabelText('Email', { exact: true }), account.email);
  await user.type(screen.getByLabelText('Mật khẩu', { exact: true }), password);
  if (mode === 'register') await user.type(screen.getByLabelText('Nhập lại mật khẩu', { exact: true }), password);
  await user.click(screen.getByRole('button', { name: mode === 'login' ? 'Đăng nhập' : 'Tạo tài khoản', exact: true }));
  await waitFor(() => expect(screen.getByTestId('repro-location').textContent).not.toMatch(/^\/dang-/));
}

beforeEach(() => {
  localStorage.clear();
  Object.defineProperty(window, 'matchMedia', { configurable: true, value: vi.fn(() => ({ matches: true })) });
  Object.defineProperty(document, 'startViewTransition', { configurable: true, value: undefined });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  Object.defineProperty(document, 'startViewTransition', { configurable: true, value: undefined });
});

it.each<Mode>(['login', 'register'])('control: direct %s returns to the exact invitation after authentication', async mode => {
  mockHttp();
  renderInvite();
  const user = userEvent.setup();
  await enterAuth(mode, user);
  await authenticate(mode, user);
  expect(screen.getByTestId('repro-location').textContent).toBe(invite);
});

const cases = (['login', 'register'] as const).flatMap(from =>
  (['header', 'footer'] as const).flatMap(place =>
    ([false, true] as const).map(transition => ({ from, to: from === 'login' ? 'register' as const : 'login' as const, place, transition }))));

it.each(cases)('retains invite after $from -> $to through $place (viewTransition=$transition)', async ({ from, to, place, transition }) => {
  const fetcher = mockHttp();
  const startTransition = vi.fn((update: () => void) => {
    update();
    return { finished: Promise.resolve() };
  });
  if (transition) {
    Object.defineProperty(window, 'matchMedia', { configurable: true, value: vi.fn(() => ({ matches: false })) });
    Object.defineProperty(document, 'startViewTransition', { configurable: true, value: startTransition });
  }
  renderInvite();
  const user = userEvent.setup();
  await enterAuth(from, user);
  const scope = document.querySelector(place === 'header' ? '.site-header' : '.auth-alternate') as HTMLElement;
  const switchLink = within(scope).getByRole('link', { name: to === 'register' ? 'Tạo tài khoản' : 'Đăng nhập', exact: true });
  await user.click(switchLink);
  await screen.findByRole('heading', { name: to === 'register' ? 'Tạo tài khoản WayFinder' : 'Đăng nhập WayFinder' });
  if (transition) expect(startTransition).toHaveBeenCalledTimes(1);
  await authenticate(to, user);
  expect(fetcher.mock.calls.filter(([url, init]) => String(url) === `/api/v1/auth/${to}` && init?.method === 'POST')).toHaveLength(1);
  // The unchanged application currently lands on /khoa-hoc here, losing invite.
  expect(screen.getByTestId('repro-location').textContent).toBe(invite);
});
