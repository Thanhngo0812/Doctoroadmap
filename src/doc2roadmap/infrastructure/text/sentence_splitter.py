# Compatibility import; the deterministic splitter is shared by chunking and anchors.
from doc2roadmap.domain.sentence_splitter import COMMON_LATIN_ABBREVIATIONS, LANGUAGE_ABBREVIATIONS, UnicodeSentenceSplitter

__all__ = ["COMMON_LATIN_ABBREVIATIONS", "LANGUAGE_ABBREVIATIONS", "UnicodeSentenceSplitter"]
