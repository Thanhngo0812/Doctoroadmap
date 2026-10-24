"""An operator approval is one exact file/profile/attempt, never a request-body flag."""
from hashlib import sha256
from io import BytesIO
import json

import pytest

from test_builds_w14 import builds, sql
from test_real_build_w15 import core
from wayfinder.infrastructure import build_spend
from wayfinder.infrastructure.real_build import RealBuildRuntime

pytestmark = pytest.mark.postgres


@pytest.fixture(autouse=True)
def deny_live_approval_transport(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Approval tests must never reach a real HTTP transport')
    monkeypatch.setattr(build_spend, 'urlopen', forbidden)


def approval(**kwargs):
    kind = getattr(build_spend, 'BuildSpendApproval', None)
    assert kind is not None, 'The exact-file operator approval boundary is missing'
    return kind(**kwargs)


def test_approved_file_is_consumed_once_in_pg_and_enables_only_that_attempt(builds, tmp_path):
    from doc2roadmap.application.ports.build import BuildRejected
    source = tmp_path / 'book.pdf'
    source.write_bytes(b'approved fake input')
    digest = sha256(source.read_bytes()).hexdigest()
    calls, receipts = [], []
    class StopPipeline:
        def __init__(self, settings, *, allow_spend, phase_b_store):
            calls.append(allow_spend)
        def usage(self):
            return dict(spent_usd=0, model_calls=0, input_tokens=0, output_tokens=0)
        def read(self, *args):
            raise BuildRejected('chu_loi', 'Stop the fake pipeline before any provider')
    runtime = RealBuildRuntime(builds.settings, builds.engine, core_settings=core(builds), pipeline_factory=StopPipeline)
    runtime.spend_approval = approval(reference='test-only-one-attempt', file_sha256=digest,
                                      pipeline_version=runtime.pipeline_version, max_usd='1')
    try:
        result = runtime.runner(receipts.append).execute(source, 'u-' + digest[:20])
        assert result.status == 'rejected' and result.spent_usd == result.model_calls == 0
        assert calls == [True] and receipts == [result]
        records = sql(builds, "SELECT value FROM phase_b_record WHERE kind='w15_build_approval' AND record_id=:ref",
                      {'ref': 'test-only-one-attempt'})
        assert len(records) == 1 and records[0]['value']['state'] == 'finished'
        with pytest.raises(ValueError, match='consumed'):
            runtime.runner(receipts.append).execute(source, 'u-' + digest[:20])
        assert calls == [True] and receipts == [result]
    finally:
        runtime.close()


@pytest.mark.parametrize('mismatch', ['file', 'doc_id', 'pipeline'])
def test_mismatched_file_identity_or_pipeline_cannot_construct_a_paid_pipeline(builds, tmp_path, mismatch):
    source = tmp_path / 'book.pdf'
    source.write_bytes(b'one approved input')
    digest = sha256(source.read_bytes()).hexdigest()
    calls = []
    def forbidden(settings, *, allow_spend, phase_b_store):
        calls.append(allow_spend)
        raise AssertionError('An unmatched approval reached pipeline construction')
    runtime = RealBuildRuntime(builds.settings, builds.engine, core_settings=core(builds), pipeline_factory=forbidden)
    runtime.spend_approval = approval(reference='test-only-mismatch-' + mismatch, file_sha256=digest,
        pipeline_version=runtime.pipeline_version if mismatch != 'pipeline' else 'a-different-pipeline', max_usd='1')
    if mismatch == 'file':
        runtime.spend_approval = approval(reference='test-only-mismatch-file',
            file_sha256=digest[:-1] + ('1' if digest[-1] == '0' else '0'),
            pipeline_version=runtime.pipeline_version, max_usd='1')
    try:
        with pytest.raises(ValueError):
            runtime.runner(lambda result: None).execute(source, 'other-doc' if mismatch == 'doc_id' else 'u-' + digest[:20])
        assert calls == []
        assert sql(builds, "SELECT count(*) AS n FROM phase_b_record WHERE kind='w15_build_approval' AND record_id=:ref",
                   {'ref': runtime.spend_approval.reference})[0]['n'] == 0
    finally:
        runtime.close()


@pytest.mark.parametrize('fault', ['none', 'audit', 'partial_usage'])
def test_real_http_adapters_use_the_approval_budget_and_record_measured_embedding_wait(builds, tmp_path, monkeypatch, fault):
    from doc2roadmap.composition_build import DocumentPipeline
    from doc2roadmap.application.ports.embedding import EmbeddingRequest
    from doc2roadmap.application.build_usage import MeteredModel
    calls, receipts = [], []
    def provider(request, *args, **kwargs):
        calls.append(request.full_url)
        if request.full_url.endswith(':predict'):
            value = {'predictions': [{'embeddings': {'values': [1.] + [0.] * 767, 'statistics': {'token_count': 100}}}]}
        else:
            value = {'candidates': [{'content': {'parts': [{'text': '{}'}]}}],
                     'usageMetadata': {'promptTokenCount': 1000}}
            if fault != 'partial_usage':
                value['usageMetadata']['candidatesTokenCount'] = 10
        return BytesIO(json.dumps(value).encode())
    monkeypatch.setattr(build_spend, 'urlopen', provider)
    monkeypatch.setattr('doc2roadmap.infrastructure.google_auth.VertexCredentials.headers', lambda self: {'Authorization': 'test-only'})
    times = iter([10., 12.])
    monkeypatch.setattr(build_spend, 'perf_counter', lambda: next(times))
    class TransportPipeline(DocumentPipeline):
        # The real HTTP clients/meters run; algorithm stages are covered by postport tests.
        def read(self, *args):
            return {'page_texts': ['Đây là giáo trình tiếng Việt có đầy đủ ví dụ. ' * 20]}
        def label_roles(self, doc):
            model = MeteredModel(self._extractor(self.settings.roadmap_model_id, max_output_tokens=32), self.usage_meter)
            model.start_session('fake test system').ask_json('fake test prompt', response_schema={'type': 'object'})
            return {}
        def a3(self, doc):
            if fault != 'partial_usage':
                self.embedding_guard.embed([EmbeddingRequest('fake embedding input', 'RETRIEVAL_DOCUMENT')])
            return {}
        def canonical(self, *args):
            return {}
        def roadmap(self, doc):
            return {'graph_version': 8}
        def learning_prep(self, *args):
            return {}
    source = tmp_path / 'source.pdf'
    source.write_bytes(b'transport-only fake source')
    digest = sha256(source.read_bytes()).hexdigest()
    runtime = RealBuildRuntime(builds.settings, builds.engine, core_settings=core(builds), pipeline_factory=TransportPipeline)
    runtime.spend_approval = approval(reference='test-only-http-adapters-' + fault, file_sha256=digest,
        pipeline_version=runtime.pipeline_version, max_usd='1', audit_log=tmp_path if fault == 'audit' else None)
    try:
        result = runtime.runner(receipts.append).execute(source, 'u-' + digest[:20])
        assert receipts == [result]
        if fault == 'none':
            assert result.status == 'succeeded' and result.usage_complete and result.model_calls == len(calls) == 2
            assert result.spent_usd == pytest.approx(.00028)
        else:
            assert result.status == 'failed' and not result.usage_complete and len(calls) == 1
            assert result.spent_usd == pytest.approx(.000265 if fault == 'audit' else .00025)
        timing = result.step_details['concepts']['web_timing']
        assert timing['embedding_wait_measured'] and timing['embedding_wait_seconds'] == (0 if fault == 'partial_usage' else 2)
        record = sql(builds, "SELECT value FROM phase_b_record WHERE kind='w15_build_approval' AND record_id=:ref",
                     {'ref': runtime.spend_approval.reference})[0]['value']
        assert record['budget']['http_calls'] == len(calls) and record['budget']['held_usd'] == '0'
        if fault == 'partial_usage':
            assert record['budget']['unknown_upper_usd'] == '0.360448'
        else:
            assert record['budget']['known_usd'] == ('0.00028' if fault == 'none' else '0.000265')
            assert record['budget']['unknown_upper_usd'] == '0'
    finally:
        runtime.close()
