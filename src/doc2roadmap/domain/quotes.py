"""Literal citation matching shared by canonical consumers and Phase B."""
import unicodedata


def quote_is_verbatim(quote, text):
    return bool(quote.strip()) and " ".join(unicodedata.normalize("NFC", quote).split()) in " ".join(
        unicodedata.normalize("NFC", text).split()
    )
