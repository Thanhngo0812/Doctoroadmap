import json

import pytest

from doc2roadmap.infrastructure.llm.gemini import GeminiExtractionSession


def test_pdf_control_characters_inside_evidence_are_preserved():
    quote = 'Tập các số hữu tỉ Q = \x1a p q | q 6= 0, p, q ∈ Z \x1b'
    raw = '{"entities":[{"name":"Số hữu tỉ","evidence":"' + quote + '"}],"edges":[]}'
    decoded = GeminiExtractionSession._decode(raw)
    assert decoded['entities'][0]['evidence'] == quote
    assert json.loads(json.dumps(decoded)) == decoded


@pytest.mark.parametrize('raw', ['{"evidence":"\x1a unfinished',
                                '{"evidence":"valid",}', '\x1a{"entities":[]}'])
def test_structurally_invalid_json_still_requires_repair(raw):
    with pytest.raises(json.JSONDecodeError):
        GeminiExtractionSession._decode(raw)
