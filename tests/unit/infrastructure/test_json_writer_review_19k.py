import io
import json

import pytest

from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore


@pytest.mark.parametrize('compact', [False, True])
def test_json_writer_keeps_exact_bytes_of_the_previous_stream_encoder(tmp_path, compact):
    payload = {'chữ': 'Tiếng Việt\n漢字\r\n', 'emoji': '🧭', 'nested': [None, True, False, {'b': 1.25, 'a': -0.0}],
               'floats': [1e-10, 1e20, float('inf'), float('nan')], 'empty': {}}
    old = io.StringIO()
    json.dump(payload, old, ensure_ascii=False, sort_keys=True, indent=None if compact else 2,
              separators=(',', ':') if compact else None)
    expected = (old.getvalue() + '\n').encode('utf-8')
    path = tmp_path / 'artifact.json'
    JsonArtifactStore._write(path, payload, compact=compact)
    assert path.read_bytes() == expected
    assert not path.with_suffix('.json.tmp').exists()
