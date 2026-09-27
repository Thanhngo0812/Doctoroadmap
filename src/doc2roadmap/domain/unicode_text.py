"""Unicode properties shared by name matching and lexical retrieval; no language dictionaries."""
import unicodedata

TEXT_RULE_VERSION = "unicode-words-unspaced-bigrams-v1"
_UNSPACED_BLOCKS = ((0x0E00,0x0EFF), (0x1000,0x109F), (0x1780,0x17FF), (0x19E0,0x19FF),
    (0x3040,0x30FF), (0x31F0,0x31FF), (0x3400,0x4DBF), (0x4E00,0x9FFF), (0xA9E0,0xA9FF),
    (0xAA60,0xAA7F), (0xF900,0xFAFF), (0xFF66,0xFF9D), (0x1AFF0,0x1AFFF), (0x1B000,0x1B16F),
    (0x20000,0x323AF))


def unspaced_character(char):
    return (unicodedata.category(char)[0] in 'LM'
            and any(start <= ord(char) <= end for start,end in _UNSPACED_BLOCKS))


def lexical_word(text):
    letters = 0
    for char in text:
        code = ord(char)
        if (0x1D400 <= code <= 0x1D7FF or 0x2100 <= code <= 0x214F
            or unicodedata.decomposition(char).startswith(('<super>', '<sub>'))):
            letters = 0
        elif unicodedata.category(char).startswith('L'):
            letters += 1
            if letters >= 2:
                return True
        elif not unicodedata.category(char).startswith('M'):
            letters = 0
    return False
