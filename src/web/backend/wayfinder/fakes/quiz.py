"""Quiz-3 generator and blind solver for zero-cost HTTP/browser checks."""
import json
from threading import Lock
from types import SimpleNamespace


class ScriptedQuizModel:
    model_id = 'gemini-3.1-flash-lite'
    is_replay = True

    def __init__(self, generator=None):
        self.generator = generator
        self.calls, self.correct, self.lock = [], {}, Lock()

    def start_session(self, system, tools=()):
        model = self
        class Session:
            def ask_json(self, prompt, **kwargs):
                with model.lock:
                    model.calls.append({'system': system, 'prompt': prompt, **kwargs})
                if model.generator is None:
                    name = prompt.split('\n', 1)[0].removeprefix('Khái niệm: ')
                    items = []
                    for number, bloom in enumerate(['nho', 'hieu', 'van_dung'], 1):
                        stem = f'{name}: phép tính $1+{number}$ có kết quả nào?'
                        options = [{'text': f'${value}$', 'why_wrong': '' if value == number + 1 else 'Cần cộng thêm một đơn vị.'}
                                   for value in range(number + 1, number + 5)]
                        items.append({'stem': stem, 'bloom': bloom, 'options': options, 'correct_index': 0,
                            'explanation': f'Ta có $1+{number}={number + 1}$.', 'source_labels': ['S1']})
                        model.correct[stem] = options[0]['text']
                    payload = {'items': items}
                else:
                    shown = json.loads(prompt.split('Các câu trắc nghiệm (phương án đánh số từ 0):\n', 1)[1])
                    payload = {'answers': [{'q': row['q'], 'chosen': row['options'].index(model.generator.correct[row['stem']]),
                        'ambiguous': False, 'reason': 'PRIVATE_SOLVER_REASON'} for row in shown]}
                return SimpleNamespace(payload=payload, usage={'promptTokenCount': 100, 'candidatesTokenCount': 60})
        return Session()
