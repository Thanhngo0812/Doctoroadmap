from types import SimpleNamespace

import pytest

from doc2roadmap.config import Settings

REMOVED = {
    'upstream_chain': 'v3', 'anchor_batch_mode': 'a5',
    'merge_description_enabled': 'true', 'merge_description_top_k': '10',
    'merge_description_min_similarity': '.9', 'canonical_repair_batch_size': '10',
}


def test_retired_experiments_are_absent_from_settings():
    assert not (set(REMOVED) & Settings.model_fields.keys())


@pytest.mark.parametrize('key,value', REMOVED.items())
def test_old_environment_options_are_ignored_with_a_named_warning(monkeypatch, key, value):
    name = 'DOC2ROADMAP_' + key.upper()
    monkeypatch.setenv(name, value)
    with pytest.warns(UserWarning, match=name):
        settings = Settings(_env_file=None)
    assert not hasattr(settings, key)


def test_old_dotenv_options_are_ignored_with_a_warning(tmp_path):
    env = tmp_path / '.env'
    env.write_text('DOC2ROADMAP_ANCHOR_BATCH_MODE=a5\nDOC2ROADMAP_CANONICAL_REPAIR_BATCH_SIZE=10\n', encoding='utf-8')
    with pytest.warns(UserWarning, match='DOC2ROADMAP_ANCHOR_BATCH_MODE'):
        settings = Settings(_env_file=env)
    assert not hasattr(settings, 'anchor_batch_mode')


@pytest.mark.parametrize('args', [
    ['a4', '--upstream-chain', 'gop'], ['roadmap', '--upstream-chain', 'v3'],
    ['a4', '--anchor-batch-mode', 'a5'],
])
def test_cli_rejects_retired_switches(args, capsys):
    from doc2roadmap.presentation.cli.main import _parser
    with pytest.raises(SystemExit) as caught:
        _parser().parse_args([*args, '--doc-id', 'book'])
    assert caught.value.code == 2 and args[1] in capsys.readouterr().err


@pytest.mark.parametrize('option,value', [
    ('upstream_chain', 'gop'), ('anchor_batch_mode', 'single'), ('nomination_config', {}),
])
def test_canonical_constructor_no_longer_accepts_retired_switches(option, value):
    from doc2roadmap.application.use_cases.canonicalize import Canonicalize
    from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
    model = SimpleNamespace(model_id='fake')
    with pytest.raises(TypeError, match=option):
        Canonicalize(object(), object(), reasoning=CanonicalReasoning(model, model), **{option: value})


def test_repair_batch_size_is_no_longer_a_constructor_option():
    from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
    with pytest.raises(TypeError, match='repair_batch_size'):
        CanonicalReasoning(None, None, repair_batch_size=10)
