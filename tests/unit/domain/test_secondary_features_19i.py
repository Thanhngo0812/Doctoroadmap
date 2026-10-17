"""19i: memoization must preserve direction-specific E5 features exactly."""
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.secondary_features import SecondaryFeatureContext, feature_rows, pair_features
from tests.unit.domain.test_secondary_features import document, fake_words


def test_all_direction_features_match_frozen_before_19i_hash():
    payload, chunks = document()
    rows = list(feature_rows(payload, chunks, fake_words))
    assert digest(rows) == 'f27b018237108d86e8ca6870039814c91258a7e2b3d8728dc995cc4b02904dab'
    assert rows[0]['x_trong_ywin_tu'] == 1 and rows[1]['x_trong_ywin_tu'] == 0


def test_context_tokenizes_each_unique_sentence_once_across_directions_and_repeated_queries(monkeypatch):
    from doc2roadmap.domain import secondary_features as features
    payload, chunks = document()
    calls, cue_calls = [], []
    original_cues = features.cues_before
    def cues(patterns, text):
        cue_calls.append(text)
        return original_cues(patterns, text)
    monkeypatch.setattr(features, 'cues_before', cues)
    def tokenize(text):
        calls.append(text)
        return fake_words(text)
    context = SecondaryFeatureContext(payload, chunks, tokenize=tokenize)
    pair = payload['suspected_pairs'][0]
    first = [pair_features(context, x, y, pair) for x, y in [('x', 'y'), ('y', 'x')]]
    assert first[0]['x_trong_ywin_tu'] == 1
    assert calls == [chunks[1].text]
    assert cue_calls == [chunks[1].text]
    calls.clear()
    again = [pair_features(context, x, y, pair) for x, y in [('y', 'x'), ('x', 'y')]]
    assert again == list(reversed(first))
    assert calls == []
    assert cue_calls == [chunks[1].text]


def test_cached_windows_are_local_to_one_document():
    payload, chunks = document()
    old = SecondaryFeatureContext(payload, chunks, tokenize=fake_words)
    original = old.window_features('x', 'y')
    chunks[1].text = 'Y là vật chất.'
    payload['nodes'][1]['anchor']['sentence'] = chunks[1].text
    current = SecondaryFeatureContext(payload, chunks, tokenize=fake_words)
    assert original['co_tu'] == 1
    assert current.window_features('x', 'y')['co_tu'] == 0
