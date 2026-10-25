"""Web boundary for W-13. The core PostgreSQL injection port must exist first."""
from inspect import signature
from time import perf_counter
from sqlalchemy.engine import make_url

from doc2roadmap.application.ports.build import BuildResult
from doc2roadmap.application.use_cases.build_document import BuildDocument
from doc2roadmap.config import Settings
from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore


class CoreBuildPortUnavailable(ValueError):
    pass


def real_settings(settings, core_settings=None):
    core = core_settings or Settings(artifact_dir=settings.artifact_root)
    if core.llm_transport != 'vertex' or not core.vertex_project or not core.vertex_location:
        raise ValueError('Real builds require Vertex transport, project and location')
    return core.model_copy(update={'artifact_dir': settings.artifact_root})


def real_pipeline_version(settings, core_settings=None):
    from doc2roadmap.composition_build import _pipeline_version
    return 'web-real:' + _pipeline_version(real_settings(settings, core_settings))


def require_store_port(factory):
    # Do not instantiate the CLI pipeline and replace store attributes afterwards.
    if 'phase_b_store' not in signature(factory).parameters:
        raise CoreBuildPortUnavailable('DocumentPipeline needs the phase_b_store injection port')


class RealBuildRuntime:
    def __init__(self, settings, engine, *, core_settings=None, pipeline_factory=None,
                 monotonic=perf_counter, spend_approval=None):
        self.settings = real_settings(settings, core_settings)
        if pipeline_factory is None:
            from doc2roadmap.composition_build import DocumentPipeline
            pipeline_factory = DocumentPipeline
        require_store_port(pipeline_factory)
        if engine.dialect.name != 'postgresql':
            raise ValueError('Real builds require the web PostgreSQL engine')
        if settings.database_url and make_url(settings.database_url).set(drivername='postgresql+psycopg') != engine.url:
            raise ValueError('Build recorder and child use cases must use the same PostgreSQL database')
        self.pipeline_factory = pipeline_factory
        self.pipeline_version = real_pipeline_version(settings, self.settings)
        self.monotonic = monotonic
        self.spend_approval = spend_approval
        self.phase_b_store = PostgresPhaseBStore(engine, lock_pool_size=settings.phase_b_lock_pool_size)

    def runner(self, recorder):
        if recorder is None:
            raise ValueError('The web build recorder is required')
        return RealBuildAdapter(self, recorder)

    def close(self):
        self.phase_b_store.close()


class RealBuildAdapter:
    def __init__(self, runtime, recorder):
        self.runtime, self.recorder = runtime, recorder

    def execute(self, file_path, doc_id, *, language='vi', progress=None, cancelled=None, dry_run=False):
        if dry_run:
            raise ValueError('Internal dry-run must not run in the build queue')
        if self.runtime.spend_approval is None:
            return self._execute(file_path, doc_id, language, progress, cancelled, allow_spend=False)
        with self.runtime.spend_approval.activate(file_path, doc_id, self.runtime) as guard:
            return self._execute(file_path, doc_id, language, progress, cancelled, allow_spend=True, spend_guard=guard)

    def _execute(self, file_path, doc_id, language, progress, cancelled, *, allow_spend, spend_guard=None):
        runtime = self.runtime
        pipeline = runtime.pipeline_factory(runtime.settings, allow_spend=allow_spend,
                                            phase_b_store=runtime.phase_b_store)
        before = pipeline.usage()
        started, timings = {}, {}

        def finish_step(step):
            if step in started:
                timings[step] = {'wall_seconds': max(0., runtime.monotonic() - started.pop(step)),
                                 'embedding_wait_seconds': spend_guard.embedding_wait(step) if spend_guard else None,
                                 'embedding_wait_measured': spend_guard is not None}

        def checkpoint(step, data):
            data = dict(data)
            if data.get('status') == 'started':
                started[step] = runtime.monotonic()
                if spend_guard:
                    spend_guard.stage = step
            elif data.get('status') == 'completed':
                finish_step(step)
                snapshot = BuildResult(doc_id, 'failed', runtime.pipeline_version)
                # Reuse W-13's baseline/missing-response rules for checkpoints and final totals.
                BuildDocument._set_usage_delta(snapshot, before, pipeline.usage())
                # Match numeric(12,6) in PostgreSQL before the next monotonic comparison.
                snapshot.spent_usd = round(snapshot.spent_usd, 6)
                data['usage'] = {key: getattr(snapshot, key) for key in
                                 ('spent_usd', 'model_calls', 'input_tokens', 'output_tokens', 'usage_complete')}
            if progress:
                progress(step, data)

        def record(result):
            result.spent_usd = round(result.spent_usd, 6)
            if spend_guard:
                budget = spend_guard.snapshot()
                result.step_details['operator_budget'] = budget
                if spend_guard.unknown:
                    result.usage_complete = False
                if spend_guard.unknown or spend_guard.stopped:
                    result.status = 'failed'
                    result.error = {'code': 'loi_noi_bo', 'message': 'Operator budget or usage requires review', 'retryable': False}
            for step in list(started):
                finish_step(step)
            for step, timing in timings.items():
                result.step_details.setdefault(step, {})['web_timing'] = timing
            self.recorder(result)

        # Direct construction avoids the CLI factory's default SQLite recorder.
        return BuildDocument(pipeline, runtime.pipeline_version, recorder=record).execute(
            file_path, doc_id, language=language, progress=checkpoint, cancelled=cancelled)
