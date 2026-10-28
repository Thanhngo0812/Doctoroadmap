import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import App from './App';
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
const first = { id: 'a', display_name: 'An', email: 'an@example.invalid', role: 'user', email_verified: false };
let account = { ...first }, posts: Array<{ url: string; body: Record<string, string>; headers: Headers }>;
let failure: { error: { code: string; fields?: Array<{ loc: string | string[]; message: string }> } } | null;
let held: ((response: Response) => void) | null, hold = false;
function Travel() { const go = useNavigate(); return <><button onClick={() => go('/muc-dung')}>Rời hồ sơ</button><button onClick={() => go('/tai-khoan')}>Mở hồ sơ</button></>; }
function page() { return render(<MemoryRouter initialEntries={['/tai-khoan']}><Travel /><App /></MemoryRouter>); }
beforeEach(() => {
  account = { ...first }; posts = []; failure = null; held = null; hold = false; localStorage.clear(); sessionStorage.clear();
  Object.defineProperty(window, 'matchMedia', { configurable: true, value: vi.fn(() => ({ matches: false, addEventListener() {}, removeEventListener() {} })) });
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open',''); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute('open'); };
  vi.stubGlobal('fetch', vi.fn(async (input, init) => {
    const url = String(input), method = init?.method ?? 'GET';
    if (url.endsWith('/me') && method === 'GET') return json({ account, csrf_token: 'fixture-csrf' });
    if (url.endsWith('/courses')) return json({ owned:[], joined:[], samples:[] });
    if (url.endsWith('/me/usage')) return json({ contract_version: 'usage-1', learner_today: { used_ratio: .2, limited: false, resets_at: '2026-10-28T00:00:00+07:00' }, builds_this_month: { used: 0, max: null, resets_at: '2026-11-01T00:00:00+07:00' }, shared_content_today: { limited: false } });
    if (method !== 'GET') {
      const body = init?.body ? JSON.parse(String(init.body)) : {};
      posts.push({url,body,headers:new Headers(init?.headers)});
      if (hold) return new Promise<Response>(resolve => { held = resolve; });
      if (failure) return json(failure, failure.error.code === 'validation' ? 422 : failure.error.code === 'csrf_failed' ? 403 : 401);
      if (url.endsWith('/me')) { account = { ...account, display_name: body.display_name.trim() }; return json({ account, csrf_token:'fixture-csrf' }); }
      if (url.endsWith('/auth/login')) { account = { ...first, id:'b', display_name:'Bình' }; return json({account,csrf_token:'other-csrf'}); }
      if (url.endsWith('/me/password')) return json({ message:'Đã đổi mật khẩu. Các phiên đăng nhập khác đã được đăng xuất.' });
      return json({message:'Đã hoàn tất.'});
    }
    throw new Error('Unexpected route '+url);
  }));
});
afterEach(() => { cleanup(); Reflect.deleteProperty(document,'startViewTransition'); vi.restoreAllMocks(); vi.unstubAllGlobals(); });
const fillPassword = async (user: ReturnType<typeof userEvent.setup>, next = 'New W04 private passphrase!') => {
  await user.type(screen.getByLabelText('Mật khẩu hiện tại'), 'Old W04 private passphrase!');
  await user.type(screen.getByLabelText('Mật khẩu mới', { exact:true }), next);
  await user.type(screen.getByLabelText('Xác nhận mật khẩu mới'), next);
};
it('saves a trimmed display name through PATCH and updates the shared account without extra private fields', async () => {
  const user=userEvent.setup();page();const name=await screen.findByLabelText('Tên hiển thị');await user.clear(name);await user.type(name,'  An Nguyễn  ');
  await user.click(screen.getByRole('button',{name:'Lưu thay đổi'}));
  expect(await screen.findByText('Đã lưu thông tin tài khoản.')).toBeVisible();
  const call=posts.find(p=>p.url.endsWith('/me'))!;expect(call.body).toEqual({display_name:'An Nguyễn'});expect(call.headers.get('X-CSRF-Token')).toBe('fixture-csrf');
  expect(screen.getByLabelText('Tài khoản của An Nguyễn')).toBeVisible();expect(screen.getByText('an@example.invalid')).toBeVisible();expect(screen.getByText('Chưa xác minh',{exact:true})).toBeVisible();
});
it('validates name after trim, rejecting 61 but accepting 60 with surrounding whitespace', async () => {
  const user=userEvent.setup();page();const name=await screen.findByLabelText('Tên hiển thị');await user.clear(name);await user.type(name,'a'.repeat(61));
  await user.click(screen.getByRole('button',{name:'Lưu thay đổi'}));expect(name).toHaveAttribute('aria-invalid','true');expect(posts).toHaveLength(0);
  await user.clear(name);await user.type(name,'  '+'a'.repeat(60)+'  ');await user.click(screen.getByRole('button',{name:'Lưu thay đổi'}));
  await waitFor(()=>expect(posts).toHaveLength(1));expect(posts[0].body.display_name).toBe('a'.repeat(60));
});
it.each(['body.display_name',['body','display_name']])('maps server fields %s to the actual field and keeps the form for correction', async loc => {
  failure={error:{code:'validation',fields:[{loc,message:'Tên này chưa hợp lệ.'}]}};
  const user=userEvent.setup();page();const name=await screen.findByLabelText('Tên hiển thị');await user.type(name,'x');await user.click(screen.getByRole('button',{name:'Lưu thay đổi'}));
  expect(await screen.findByText('Tên này chưa hợp lệ.')).toHaveAttribute('id','profile-display-name-error');expect(name).toHaveAttribute('aria-invalid','true');
});
it('wrong current password marks that field without logging out or clearing the typed new password', async () => {
  failure={error:{code:'invalid_credentials'}};const user=userEvent.setup();page();await screen.findByLabelText('Tên hiển thị');await fillPassword(user);
  await user.click(screen.getByRole('button',{name:'Đổi mật khẩu'}));
  expect(await screen.findByText('Mật khẩu hiện tại chưa đúng.')).toHaveAttribute('id','profile-current-password-error');expect(screen.getByLabelText('Mật khẩu hiện tại')).toHaveAttribute('aria-invalid','true');
  expect(screen.getByRole('heading',{name:'Tài khoản của bạn'})).toBeVisible();expect(screen.getByLabelText('Mật khẩu mới',{exact:true})).toHaveValue('New W04 private passphrase!');
});
it('requires confirmation, clears secrets after successful change and keeps the current account', async () => {
  const user=userEvent.setup();page();await screen.findByLabelText('Tên hiển thị');await fillPassword(user);
  await user.clear(screen.getByLabelText('Xác nhận mật khẩu mới'));await user.type(screen.getByLabelText('Xác nhận mật khẩu mới'),'Mismatch');await user.click(screen.getByRole('button',{name:'Đổi mật khẩu'}));
  expect(screen.getByLabelText('Xác nhận mật khẩu mới')).toHaveAttribute('aria-invalid','true');expect(posts).toHaveLength(0);
  await user.clear(screen.getByLabelText('Xác nhận mật khẩu mới'));await user.type(screen.getByLabelText('Xác nhận mật khẩu mới'),'New W04 private passphrase!');await user.click(screen.getByRole('button',{name:'Đổi mật khẩu'}));
  expect(await screen.findByText(/Đã đổi mật khẩu/)).toBeVisible();for(const name of ['Mật khẩu hiện tại','Mật khẩu mới','Xác nhận mật khẩu mới'])expect(screen.getByLabelText(name,{exact:true})).toHaveValue('');
  expect(posts[0].body).toEqual({current_password:'Old W04 private passphrase!',new_password:'New W04 private passphrase!'});
  expect(screen.getByRole('heading',{name:'Tài khoản của bạn'})).toBeVisible();expect(JSON.stringify(localStorage)+JSON.stringify(sessionStorage)+location.href).not.toMatch(/W04 private/);
});
it('confirms logout-all before POST and safely removes the private page', async () => {
  const user=userEvent.setup();page();await screen.findByLabelText('Tên hiển thị');await user.click(screen.getByRole('button',{name:'Đăng xuất khỏi mọi thiết bị'}));
  const dialog=screen.getByRole('dialog',{name:'Đăng xuất khỏi mọi thiết bị?'});expect(dialog).toBeVisible();expect(posts).toHaveLength(0);
  await user.click(screen.getByRole('button',{name:'Giữ đăng nhập'}));expect(dialog).not.toBeInTheDocument();expect(posts).toHaveLength(0);
  await user.click(screen.getByRole('button',{name:'Đăng xuất khỏi mọi thiết bị'}));await user.click(screen.getByRole('button',{name:'Xác nhận đăng xuất'}));
  expect(await screen.findByRole('heading',{name:/Đăng nhập/})).toBeVisible();expect(posts.at(-1)?.url).toBe('/api/v1/auth/logout-all');expect(screen.queryByLabelText('Tên hiển thị')).not.toBeInTheDocument();
});
it('does not retain password state or apply a delayed profile response after leaving the route', async () => {
  const user=userEvent.setup();page();const name=await screen.findByLabelText('Tên hiển thị');await fillPassword(user);await user.clear(name);await user.type(name,'Tên cũ về muộn');hold=true;
  await user.click(screen.getByRole('button',{name:'Lưu thay đổi'}));await waitFor(()=>expect(held).toBeTypeOf('function'));const old=held!;
  hold=false;await user.click(screen.getByRole('button',{name:'Rời hồ sơ'}));await screen.findByText('Hôm nay đã dùng 20%');
  await act(async()=>old(json({account:{...first,display_name:'Tên cũ về muộn'},csrf_token:'old-csrf'})));
  await user.click(screen.getByRole('button',{name:'Mở hồ sơ'}));expect(await screen.findByLabelText('Tên hiển thị')).toHaveValue('An');expect(screen.getByLabelText('Mật khẩu mới',{exact:true})).toHaveValue('');
});

it('a profile refresh from the old session cannot resurrect A after logout-all and login as B', async () => {
  const original = globalThis.fetch; let meCalls = 0; let release!: (response: Response) => void;
  vi.stubGlobal('fetch', vi.fn((input, init) => {
    if (String(input).endsWith('/me') && (!init?.method || init.method === 'GET') && ++meCalls === 2)
      return new Promise<Response>(resolve => { release = resolve; });
    return original(input, init);
  }));
  const user=userEvent.setup();page();await screen.findByLabelText('Tên hiển thị');await waitFor(()=>expect(release).toBeTypeOf('function'));
  await user.click(screen.getByRole('button',{name:'Đăng xuất khỏi mọi thiết bị'}));await user.click(screen.getByRole('button',{name:'Xác nhận đăng xuất'}));
  await screen.findByRole('heading',{name:/Đăng nhập/});await user.type(screen.getByLabelText('Email',{exact:true}),'binh@example.invalid');await user.type(screen.getByLabelText('Mật khẩu',{exact:true}),'Other W04 private passphrase!');
  await user.click(screen.getByRole('button',{name:'Đăng nhập'}));await screen.findByLabelText('Tài khoản của Bình');
  await act(async()=>release(json({account:first,csrf_token:'stale-a-csrf'})));
  expect(screen.getByLabelText('Tài khoản của Bình')).toBeVisible();expect(screen.queryByLabelText('Tài khoản của An')).not.toBeInTheDocument();
});

it('finishes logout-all for the current session even if the profile unmounts before the view transition callback', async () => {
  const updates: Array<() => void> = [];
  Object.defineProperty(document,'startViewTransition',{configurable:true,value:(update:()=>void)=>{updates.push(update);return {finished:Promise.resolve()};}});
  const user=userEvent.setup();page();await screen.findByLabelText('Tên hiển thị');await user.click(screen.getByRole('button',{name:'Đăng xuất khỏi mọi thiết bị'}));await user.click(screen.getByRole('button',{name:'Xác nhận đăng xuất'}));
  await waitFor(()=>expect(updates).toHaveLength(1));await user.click(screen.getByRole('button',{name:'Rời hồ sơ'}));await screen.findByText('Hôm nay đã dùng 20%');
  await act(async()=>updates[0]());expect(await screen.findByRole('heading',{name:/Đăng nhập/})).toBeVisible();
});
