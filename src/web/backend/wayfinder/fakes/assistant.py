"""Scripted tool-stream provider for web tests; no credentials or network client."""
from threading import Event, Lock
from types import SimpleNamespace

from doc2roadmap.application.ports.phase_b import Delta, Done, ToolCall


class ScriptedAssistantModel:
    model_id = 'gemini-3.1-flash-lite'
    is_replay = True

    def __init__(self, *, scenario='normal', pause=False):
        self.scenario, self.pause = scenario, pause
        self.calls, self.systems = [], []
        self.waiting, self.release, self.lock = Event(), Event(), Lock()

    def start_session(self, system, tools=()):
        model = self
        self.systems.append((system, tools))
        class Session:
            def __init__(self):
                self.round = 0
                self.last_usage = {'input_tokens': 100, 'output_tokens': 40}

            def stream(self, messages, *, mode='AUTO'):
                with model.lock:
                    call = SimpleNamespace(finished=False, messages=messages, mode=mode)
                    model.calls.append(call)
                try:
                    if model.scenario == 'failure':
                        raise ConnectionError('scripted private transport error')
                    if model.scenario == 'tools' and self.round == 0:
                        yield ToolCall('make_quiz', {'scope': 'module 1', 'n': 1, 'owner': 'forged-model-owner'}, 'quiz')
                        yield ToolCall('make_document', {'request': 'Tóm tắt bài học', 'scope': 'module này'}, 'doc')
                    else:
                        yield Delta('Theo sách, một tập hợp gồm các phần tử. [S1]\n\n')
                        model.waiting.set()
                        if model.pause and not model.release.wait(15):
                            raise TimeoutError('fake model release timed out')
                        if model.scenario == 'tail':
                            raise ConnectionError('scripted private tail error')
                        yield Delta('Ta có $x^2+y^2$ và $$1+1=2.$$ [S999]\n\n')
                        yield Delta('[Quiz tự bịa](quiz:made-up) [URL tự bịa](/khoa-hoc/other/quizzes/made-up).')
                    self.round += 1
                    yield Done(self.last_usage, finish_reason='STOP')
                finally:
                    call.finished = True
        return Session()
