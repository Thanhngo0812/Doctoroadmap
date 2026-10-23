"""Fake worker by default; real composition requires the core PostgreSQL port."""
import os
from pathlib import Path
from threading import Event
from uuid import uuid4

APPROVED_MANIFESTS={
    '5fc819f723f7263fe3d443ec780009a75aae66f2c35db8fe0bc3e3c50464eb84',
    '4f81f6d0f04e64bd02257aa873f9d68145bc121ec6e1ecf10d819458ed4d4a5a',
}


def run_worker(worker,*,once=False,stop=None):
    stop=stop or Event()
    while not stop.is_set():
        job=worker.run_next_job()
        if once: return 0
        if job is None: stop.wait(3)
    return 0


def make_worker(settings,*,source_doc=None,fixture_root=None,manifest=None,manifest_sha256=None,media=None,mailer=None):
    from doc2roadmap.application.phase_b.retrieval import load_learning_graph
    from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
    from wayfinder.application.build_worker import BuildWorker
    from wayfinder.composition import compose_build_service
    from wayfinder.fakes.mail import FakeMailer
    from wayfinder.infrastructure.database import create_database_engine
    from wayfinder.infrastructure.fake_build import ManifestFakeBuildRunner

    if settings.build_runner=='real':
        return make_real_worker(settings,media=media,mailer=mailer)
    if settings.env!='dev': raise ValueError('W-14 fake worker is development-only')
    if manifest_sha256 not in APPROVED_MANIFESTS: raise ValueError('Use a frozen development manifest')
    if not settings.database_url: raise ValueError('PostgreSQL is required')
    ManifestFakeBuildRunner(fixture_root,settings.artifact_root,source_doc,
        manifest=manifest,manifest_sha256=manifest_sha256)
    engine=create_database_engine(settings.database_url)
    service=compose_build_service(settings,engine,media=media)
    def factory(recorder):
        return ManifestFakeBuildRunner(fixture_root,settings.artifact_root,source_doc,
            manifest=manifest,manifest_sha256=manifest_sha256,recorder=recorder,pipeline_version=service.pipeline_version)
    worker=BuildWorker(service,runner_factory=factory,
        graph_loader=lambda doc,version:load_learning_graph(JsonArtifactStore(settings.artifact_root),doc,version),
        mailer=mailer if mailer is not None else FakeMailer(),
        worker_id=f'{os.getpid()}-{uuid4().hex}')
    return worker,engine


def make_real_worker(settings,*,media=None,mailer=None,core_settings=None,pipeline_factory=None,graph_loader=None):
    from doc2roadmap.application.phase_b.retrieval import load_learning_graph
    from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
    from wayfinder.application.build_worker import BuildWorker
    from wayfinder.composition import compose_build_service
    from wayfinder.fakes.mail import FakeMailer
    from wayfinder.infrastructure.database import create_database_engine
    from wayfinder.infrastructure.real_build import RealBuildRuntime

    if not settings.database_url: raise ValueError('PostgreSQL is required')
    engine=create_database_engine(settings.database_url)
    runtime=None
    try:
        runtime=RealBuildRuntime(settings,engine,core_settings=core_settings,pipeline_factory=pipeline_factory)
        service=compose_build_service(settings,engine,media=media,core_settings=runtime.settings)
        loader=graph_loader or (lambda doc,version:load_learning_graph(JsonArtifactStore(settings.artifact_root),doc,version))
        worker=BuildWorker(service,runner_factory=runtime.runner,graph_loader=loader,
            mailer=mailer if mailer is not None else FakeMailer(),worker_id=f'{os.getpid()}-{uuid4().hex}')
        worker.build_runtime=runtime
        return worker,engine
    except Exception:
        if runtime: runtime.close()
        engine.dispose()
        raise


def main(settings,*,source_doc=None,fixture_root=None,manifest=None,manifest_sha256=None,once=False):
    worker,engine=make_worker(settings,source_doc=source_doc,fixture_root=Path(fixture_root) if fixture_root is not None else None,
        manifest=Path(manifest) if manifest is not None else None,manifest_sha256=manifest_sha256)
    try: return run_worker(worker,once=once)
    finally:
        close=getattr(worker.mailer,'close',None)
        if close: close()
        runtime=getattr(worker,'build_runtime',None)
        if runtime: runtime.close()
        engine.dispose()
