from http.client import IncompleteRead
from io import BytesIO
from urllib.request import Request

import pytest

from doc2roadmap.application.ports.embedding import EmbeddingRequest
from doc2roadmap.infrastructure.embedding.gemini import GeminiEmbedding
from doc2roadmap.infrastructure.google_auth import VertexCredentials
from doc2roadmap.infrastructure.llm.gemini import GeminiEntityExtractor
from doc2roadmap.infrastructure.llm.rate_limit import AdaptiveModelLimiter


def unexpected_wait(_):
    pytest.fail('a finished request still holds a permit')


@pytest.mark.parametrize('client', ['llm', 'embedding'])
@pytest.mark.parametrize('error', [IncompleteRead(b'partial', 20), ConnectionResetError('reset'),
                                  ValueError('unexpected'), KeyboardInterrupt()])
def test_every_exit_returns_permit(client, error, monkeypatch):
    gate = AdaptiveModelLimiter(2, 1000000, sleeper=unexpected_wait)
    monkeypatch.setattr(VertexCredentials, 'headers', lambda self: {})
    module = 'doc2roadmap.infrastructure.' + ('llm' if client == 'llm' else 'embedding') + '.gemini'

    class BrokenResponse(BytesIO):
        def read(self, *args):
            raise error

    monkeypatch.setattr(module + '.urlopen', lambda *a, **kw: BrokenResponse())
    if client == 'llm':
        model = GeminiEntityExtractor('fake', limiter=gate, max_retries=0)
        call = lambda: model._post(Request('https://example.invalid', data=b'{}'), estimated_tokens=1)
    else:
        model = GeminiEmbedding(None, transport='vertex', vertex_project='fake',
                                limiter=gate, max_retries=0)
        call = lambda: model._embed_vertex(EmbeddingRequest('alpha', 'SEMANTIC_SIMILARITY'))
    with pytest.raises(BaseException):
        call()
    # Independent consequence: both slots can immediately be acquired again.
    permits = [gate.acquire(1), gate.acquire(1)]
    for permit in permits:
        gate.release(permit, success=True)


@pytest.mark.parametrize('client', ['llm', 'embedding'])
def test_partial_http_body_is_retried_then_releases_slots(client, monkeypatch):
    gate = AdaptiveModelLimiter(2, 1000000, sleeper=unexpected_wait)
    monkeypatch.setattr(VertexCredentials, 'headers', lambda self: {})
    module = 'doc2roadmap.infrastructure.' + ('llm' if client == 'llm' else 'embedding') + '.gemini'
    calls = []

    class Partial(BytesIO):
        def read(self, *args):
            raise IncompleteRead(b'partial', 20)

    def open_response(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            return Partial()
        return BytesIO(b'{"predictions":[{"embeddings":{"values":[3,4]}}]}')

    monkeypatch.setattr(module + '.urlopen', open_response)
    monkeypatch.setattr(module + '.sleep', lambda seconds: None)
    if client == 'llm':
        model = GeminiEntityExtractor('fake', limiter=gate, max_retries=1)
        assert model._post(Request('https://example.invalid', data=b'{}'), estimated_tokens=1)[0]
    else:
        model = GeminiEmbedding(None, transport='vertex', vertex_project='fake',
                                limiter=gate, max_retries=1, output_dimensionality=2)
        assert model._embed_vertex(EmbeddingRequest('alpha', 'SEMANTIC_SIMILARITY')) == [0.6, 0.8]
    assert len(calls) == 2
    permits = [gate.acquire(1), gate.acquire(1)]
    for permit in permits:
        gate.release(permit, success=True)
