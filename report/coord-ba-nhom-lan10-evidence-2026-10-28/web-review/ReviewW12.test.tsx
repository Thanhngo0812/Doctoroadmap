import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { AuthPage, AuthProvider } from './Auth';
import { EmailInvitations, InvitationsInbox } from './Invitations';

const account={id:'owner',email:'owner@example.invalid',display_name:'Owner',role:'user',email_verified:true};
const item={id:'created',course_id:'course',course_title:'Independent course',email:'new@example.invalid',status:'pending',expires_at:'2026-11-03T08:00:00Z',created_at:'2026-10-27T08:00:00Z',responded_at:null};
const json=(body:unknown)=>new Response(JSON.stringify(body),{headers:{'content-type':'application/json'}});
let requests:Array<{url:string;method:string;body:unknown}>;
let verified:boolean;
beforeEach(()=>{
  verified=true;requests=[];localStorage.clear();sessionStorage.clear();
  Object.defineProperty(window,'matchMedia',{configurable:true,value:()=>({matches:false,addEventListener(){},removeEventListener(){}})});
  vi.stubGlobal('fetch',vi.fn(async(input,init)=>{
    const url=String(input),method=init?.method??'GET',body=init?.body?JSON.parse(String(init.body)):null;requests.push({url,method,body});
    if(url.endsWith('/me'))return json({account:{...account,email_verified:verified},csrf_token:'synthetic-csrf'});
    if(url.endsWith('/invitations'))return json({items:method==='POST'?[item]:[]});
    throw Error('Unexpected offline route '+url);
  }));
});
afterEach(()=>{cleanup();vi.unstubAllGlobals();vi.restoreAllMocks();});
function mount(child:React.ReactNode){return render(<MemoryRouter><AuthProvider>{child}</AuthProvider></MemoryRouter>);}
it('review regression: a list response started before POST cannot erase the newly created invitation',async()=>{
  const base=globalThis.fetch;let release!:(r:Response)=>void;
  vi.stubGlobal('fetch',vi.fn((input,init)=>String(input).endsWith('/invitations')&&(!init?.method||init.method==='GET')?new Promise<Response>(r=>{release=r;}):base(input,init)));
  mount(<EmailInvitations courseId="course"/>);await waitFor(()=>expect(release).toBeTypeOf('function'));
  fireEvent.change(screen.getByLabelText('Email người nhận'),{target:{value:item.email}});fireEvent.click(screen.getByRole('button',{name:'Gửi lời mời'}));
  expect(await screen.findByText(/Đã tạo 1 lời mời/)).toBeVisible();
  await act(async()=>release(json({items:[]})));
  expect(screen.getByText(item.email)).toBeVisible();
  expect(screen.queryByText('Chưa có lời mời đang chờ.')).not.toBeInTheDocument();
});
it('review: exactly 50 distinct addresses reach the actual API contract once',async()=>{
  mount(<EmailInvitations courseId="course"/>);await screen.findByText('Chưa có lời mời đang chờ.');
  const emails=Array.from({length:50},(_,i)=>`person${i}@example.invalid`);
  fireEvent.change(screen.getByLabelText('Email người nhận'),{target:{value:emails.join('\n')}});fireEvent.click(screen.getByRole('button',{name:'Gửi lời mời'}));
  await screen.findByText(/Đã tạo 1 lời mời/);expect(requests.filter(r=>r.method==='POST')).toEqual([{url:'/api/v1/courses/course/invitations',method:'POST',body:{emails}}]);
  expect(screen.getByText(item.email)).toBeVisible();expect(screen.getByRole('button',{name:'Huỷ lời mời cho '+item.email})).toBeEnabled();
  expect(screen.queryByText('Chưa có lời mời đang chờ.')).not.toBeInTheDocument();
});
function Inbox(){return <InvitationsInbox onJoined={()=>{throw Error('Unverified account joined');}}/>;}
it('review: an unverified account makes no inbox request and exposes no accept control',async()=>{
  verified=false;mount(<SafeInbox/>);await screen.findByText(/Xác minh đúng email nhận lời mời để xem/);
  expect(requests.some(r=>r.url.endsWith('/me/invitations'))).toBe(false);expect(screen.queryByRole('button',{name:/Chấp nhận/})).not.toBeInTheDocument();
});
import { useAuth } from './Auth';
function SafeInbox(){return useAuth().account?<Inbox/>:null;}
function Location(){const location=useLocation();return <output aria-label="review URL">{location.pathname+location.search+location.hash}</output>;}
it('review: actual AuthPage removes raw fragment before any invitation API request',async()=>{
  vi.stubGlobal('fetch',vi.fn(async(input,init)=>{requests.push({url:String(input),method:init?.method??'GET',body:init?.body??null});return new Response(JSON.stringify({error:{code:'unauthenticated'}}),{status:401,headers:{'content-type':'application/json'}});}));
  render(<MemoryRouter initialEntries={['/dang-ky#invitation=REVIEW_RAW_TOKEN']}><AuthProvider><Location/><Routes><Route path="/dang-ky" element={<AuthPage mode="register" theme="light" onToggleTheme={()=>{}}/>}/></Routes></AuthProvider></MemoryRouter>);
  await waitFor(()=>expect(screen.getByLabelText('review URL')).toHaveTextContent(/^\/dang-ky$/));
  expect(screen.getByText(/Đăng ký không tự tham gia khoá học/)).toBeVisible();expect(JSON.stringify(requests)+JSON.stringify(localStorage)+JSON.stringify(sessionStorage)).not.toContain('REVIEW_RAW_TOKEN');
  expect(requests.map(r=>r.url)).toEqual(['/api/v1/me']);
});
