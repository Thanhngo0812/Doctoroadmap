import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from './Auth';
import { apiFetch } from './api';

const A = {id:'A',email:'a@example.invalid',display_name:'Alice',role:'user',email_verified:true};
const B = {...A,id:'B',email:'b@example.invalid',display_name:'Bob'};
const json = (value: unknown) => new Response(JSON.stringify(value),{headers:{'content-type':'application/json'}});
let session: ReturnType<typeof useAuth>;
let headers: Headers;
function Probe() { session=useAuth(); return <output aria-label="review identity">{session.account?.email ?? session.status}</output>; }
beforeEach(()=>{
  Object.defineProperty(window,'matchMedia',{configurable:true,value:()=>({matches:false,addEventListener(){},removeEventListener(){}})});
  vi.stubGlobal('fetch',vi.fn(async(input,init)=>{
    const url=String(input);
    if(url.endsWith('/auth/login'))return json({account:B,csrf_token:'csrf-B'});
    if(url.endsWith('/auth/logout-all'))return json({message:'Logged out everywhere'});
    if(url.endsWith('/me'))return json({account:A,csrf_token:'csrf-A'});
    headers=new Headers(init?.headers);return json({message:'recorded'});
  }));
});
afterEach(()=>{cleanup();Reflect.deleteProperty(document,'startViewTransition');vi.unstubAllGlobals();vi.restoreAllMocks();});
function mount(){render(<MemoryRouter><AuthProvider><Probe/></AuthProvider></MemoryRouter>);}
async function loginB(){await act(async()=>{session.clearSession();});await act(async()=>{await session.login(B.email,'synthetic password');});}
async function assertB(){expect(screen.getByLabelText('review identity')).toHaveTextContent(B.email);await apiFetch('/review/observe',{method:'POST'});expect(headers.get('X-CSRF-Token')).toBe('csrf-B');}
it('review: stale successful refresh cannot replace B identity or its CSRF header',async()=>{
  mount();await screen.findByText(A.email);
  const oldFetch=globalThis.fetch;let release!:(r:Response)=>void;
  vi.stubGlobal('fetch',vi.fn((input,init)=>String(input).endsWith('/me')?new Promise<Response>(r=>{release=r;}):oldFetch(input,init)));
  let pending!:Promise<unknown>;act(()=>{pending=session.refresh();});await waitFor(()=>expect(release).toBeTypeOf('function'));
  await loginB();await act(async()=>{release(json({account:A,csrf_token:'stale-A'}));await pending;});await assertB();
});
it('review: delayed profile PATCH from A cannot replace B identity or its CSRF header',async()=>{
  mount();await screen.findByText(A.email);
  const oldFetch=globalThis.fetch;let release!:(r:Response)=>void;
  vi.stubGlobal('fetch',vi.fn((input,init)=>init?.method==='PATCH'?new Promise<Response>(r=>{release=r;}):oldFetch(input,init)));
  let pending!:Promise<unknown>;act(()=>{pending=session.updateProfile('Changed A',new AbortController().signal);});await waitFor(()=>expect(release).toBeTypeOf('function'));
  await loginB();await act(async()=>{release(json({account:{...A,display_name:'Changed A'},csrf_token:'stale-A'}));await pending;});await assertB();
});
it('review: queued logout-all transition for A cannot clear the later B session',async()=>{
  let callback!:(()=>void);
  Object.defineProperty(document,'startViewTransition',{configurable:true,value:(fn:()=>void)=>{callback=fn;return{finished:Promise.resolve()};}});
  mount();await screen.findByText(A.email);await act(async()=>{await session.logoutAll(new AbortController().signal);});
  await loginB();await act(async()=>callback());await assertB();
});
