import re

from .ports import TextSpan


COMMON_LATIN_ABBREVIATIONS = frozenset(
    {
        "Dr.",
        "Mr.",
        "Mrs.",
        "Ms.",
        "Prof.",
        "e.g.",
        "i.e.",
        "et al.",
        "cf.",
        "vs.",
        "Fig.",
        "Eq.",
        "Sec.",
        "Vol.",
        "No.",
        "p.",
        "pp.",
    }
)
LANGUAGE_ABBREVIATIONS = {
    "vi": frozenset({"PGS.", "ThS.", "TS.", "GS.", "TP."}),
}


class UnicodeSentenceSplitter:
    _placeholder = "\ue000"
    _decimal = re.compile(r"(?<=\d)\.(?=\d)")
    _closers = r'''["')\]”’）】》」』]*'''
    _boundary = re.compile(
        rf"(?:[.!?…]+{_closers}(?=\s|$)|[。！？।॥؟۔។៕]+{_closers})"
    )
    _abbreviation = re.compile(
        "(?<!\\w)(?:"
        + "|".join(
            re.escape(value)
            for value in sorted(
                COMMON_LATIN_ABBREVIATIONS.union(*LANGUAGE_ABBREVIATIONS.values()),
                key=len,
                reverse=True,
            )
        )
        + ")",
        re.IGNORECASE,
    )

    def split(self, text: str) -> list[TextSpan]:
        masked = self._abbreviation.sub(
            lambda match: match.group(0).replace(".", self._placeholder),
            text,
        )
        masked = self._decimal.sub(self._placeholder, masked)
        spans: list[TextSpan] = []
        start = 0
        for match in self._boundary.finditer(masked):
            end = match.end()
            next_meaningful = end
            while next_meaningful < len(text) and not text[next_meaningful].isalnum():
                next_meaningful += 1
            if next_meaningful < len(text) and text[next_meaningful].islower():
                continue
            while start < end and text[start].isspace():
                start += 1
            if start < end:
                spans.append(TextSpan(start, end))
            start = end
        while start < len(text) and text[start].isspace():
            start += 1
        if start < len(text):
            spans.append(TextSpan(start, len(text)))
        return spans
