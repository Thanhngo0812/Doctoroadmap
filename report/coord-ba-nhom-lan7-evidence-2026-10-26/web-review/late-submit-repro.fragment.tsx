
it('R7 ignores a late submission result after browser history opens another attempt', async () => {
  let resolveSubmit!: (r: Response) => void;
  const pending = new Promise<Response>(resolve => { resolveSubmit = resolve; });
  const original = vi.mocked(fetch).getMockImplementation()!;
  const second = { ...quiz, attempt_id: 'qa_2', items: [{...item, stem: 'Attempt two question'}] };
  vi.mocked(fetch).mockImplementation((input, init) => String(input).endsWith('/quizzes/qa_1/submit')
    ? pending : String(input).endsWith('/quizzes/qa_2') ? Promise.resolve(json(second)) : original(input, init));
  function HistoryBack() { const navigate = useNavigate(); return <button onClick={() => navigate(-1)}>History back</button>; }
  render(<MemoryRouter initialEntries={['/khoa-hoc/c/quiz/qa_2','/khoa-hoc/c/quiz/qa_1']} initialIndex={1}><HistoryBack /><App /></MemoryRouter>);
  await screen.findByRole('button', { name: 'Nộp bài' });
  await userEvent.click(screen.getByRole('button', { name: 'Nộp bài' }));
  await userEvent.click(screen.getByRole('button', { name: 'History back' }));
  await screen.findByText('Attempt two question');
  await act(async () => { resolveSubmit(json(result)); });
  expect(screen.queryByRole('heading', { name: 'Kết quả quiz' })).not.toBeInTheDocument();
  expect(screen.getByText('Attempt two question')).toBeVisible();
});
