"""The operator harness must refuse money before any DB or provider composition."""
import json
from decimal import Decimal
from hashlib import sha256
from uuid import uuid4

import pytest

import w15_operator_run as operator
from test_builds_w14 import builds
from test_pipeline_postport_w15 import fake_providers, guarded_pg, source_pdf, Model, Embedding


@pytest.mark.parametrize('approved', [False, None, 'true', 1])
def test_operator_rejects_missing_or_non_boolean_owner_approval_before_composition(tmp_path, monkeypatch, approved):
    plan, approval = tmp_path / 'plan.json', tmp_path / 'approval.json'
    plan.write_text('{}', encoding='utf-8')
    approval.write_text(json.dumps({'approved': approved, 'approved_by': 'project-owner'}), encoding='utf-8')
    def forbidden(*args, **kwargs):
        raise AssertionError('An unapproved run reached DB or model composition')
    monkeypatch.setattr(operator, 'profile', forbidden)
    monkeypatch.setattr(operator, 'create_database_engine', forbidden)
    with pytest.raises(ValueError, match='project owner'):
        operator.execute(plan, approval)


@pytest.mark.parametrize('field', ['file_sha256', 'pipeline_version', 'database'])
def test_operator_rejects_any_difference_from_the_dry_run_before_composition(tmp_path, monkeypatch, field):
    data = {'file_sha256': 'a' * 64, 'pipeline_version': 'one-profile', 'database': 'one-prepared-db'}
    plan, approval = tmp_path / 'plan.json', tmp_path / 'approval.json'
    plan.write_text(json.dumps(data), encoding='utf-8')
    permission = {**data, field: 'a-different-value', 'approved': True, 'approved_by': 'project-owner'}
    approval.write_text(json.dumps(permission), encoding='utf-8')
    def forbidden(*args, **kwargs):
        raise AssertionError('A mismatched run reached composition')
    monkeypatch.setattr(operator, 'profile', forbidden)
    monkeypatch.setattr(operator, 'create_database_engine', forbidden)
    with pytest.raises(ValueError, match='differs'):
        operator.execute(plan, approval)


def test_operator_bootstrap_then_web_ready_mail_uses_the_new_cache_without_more_fake_calls(builds, fake_providers, monkeypatch):
    from doc2roadmap.config import Settings
    from wayfinder.infrastructure.real_build import RealBuildRuntime
    nonce = uuid4().hex[:12]
    run_dir = operator.ROOT / 'tmp' / ('w15-operator-doc-6-' + nonce)
    run_dir.mkdir()
    content = source_pdf()
    (run_dir / 'source.pdf').write_bytes(content)
    digest = sha256(content).hexdigest()
    settings = builds.settings.model_copy(update={'artifact_root': run_dir / 'artifacts', 'build_runner': 'real',
        'database_url': builds.postgres_database_url.render_as_string(hide_password=False)})
    core = Settings(_env_file=None, artifact_dir=settings.artifact_root, llm_transport='vertex',
                    vertex_project='fake-only', vertex_location='global', secondary_mode='llm')
    runtime = RealBuildRuntime(settings, builds.engine, core_settings=core)
    try:
        version = runtime.pipeline_version
    finally:
        runtime.close()
    data = dict(book='doc-6', run_dir=run_dir.relative_to(operator.ROOT).as_posix(), database='wayfinder_w15_' + nonce,
                file_sha256=digest, pipeline_version=version)
    plan, permission = run_dir / 'plan.json', run_dir / 'fake-approval.json'
    plan.write_text(json.dumps(data), encoding='utf-8')
    permission.write_text(json.dumps({**data, 'reference': 'fake-only-operator-' + nonce, 'max_usd': '1',
        'approved': True, 'approved_by': 'project-owner'}), encoding='utf-8')
    monkeypatch.setattr(operator, 'profile', lambda *args: (settings, core))
    monkeypatch.setattr(operator, 'test_database_url', lambda *args: builds.postgres_database_url)
    def forbidden(*args, **kwargs):
        raise AssertionError('The synthetic operator test must never use a live transport')
    monkeypatch.setattr('wayfinder.infrastructure.build_spend.urlopen', forbidden)
    operator.execute(plan, permission)
    result = json.loads((run_dir / 'execution.json').read_text(encoding='utf-8'))
    assert result['bootstrap']['status'] == result['build']['status'] == 'succeeded'
    assert result['bootstrap']['model_calls'] == len(Model.calls) + Embedding.calls > 0
    assert result['build']['model_calls'] == 0 and Decimal(result['build']['spent_usd']) == 0
    assert len(result['courses']) == 1 and result['courses'][0]['status'] == 'ready'
    assert result['mail_subjects'] == ['Bản dựng xong']
    assert 'operator_budget' not in json.dumps(result['http_build']) and 'spent_usd' not in json.dumps(result['http_build'])
