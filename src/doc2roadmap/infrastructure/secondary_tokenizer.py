"""Offline CRF word segmentation, with a document-local sentence cache."""
from functools import lru_cache


class VietnameseWordTokenizer:
    identifier = "underthesea:9.5.0:ws_crf_vlsp2013_20230727:syllable-normalized-v1"

    @lru_cache(maxsize=32768)
    def __call__(self, sentence):
        from underthesea import word_tokenize

        return tuple(word_tokenize(sentence))
