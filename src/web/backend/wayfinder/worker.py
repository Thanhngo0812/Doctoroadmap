"""W-14 worker command. W-15 is required before a real runner can be selected."""
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


def make_worker(settings,*,source_doc,fixture_root,manifest,manifest_sha256,media=None,mailer=None):
    from doc2roadmap.application.phase_b.retrieval import load_learning_graph
    from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
    from wayfinder.application.build_worker import BuildWorker
    from wayfinder.composition import compose_build_service
    from wayfinder.fakes.mail import FakeMailer
    from wayfinder.infrastructure.database import create_database_engine
    from wayfinder.infrastructure.fake_build import ManifestFakeBuildRunner

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


def main(settings,*,source_doc,fixture_root,manifest,manifest_sha256,once=False):
    worker,engine=make_worker(settings,source_doc=source_doc,fixture_root=Path(fixture_root),
        manifest=Path(manifest),manifest_sha256=manifest_sha256)
    try: return run_worker(worker,once=once)
    finally:
        close=getattr(worker.mailer,'close',None)
        if close: close()
        engine.dispose()
