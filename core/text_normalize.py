"""
Canonical Arabic/Persian text normalization for narrator matching.

Two bugs motivated this module, both found in the copy-pasted narrator-lookup
block that used to live in rijal_service.py, ijtihad_service.py and
conflict_resolver_service.py:

1. `.replace("ا", "أ")` replaced EVERY alef, including medial ones, producing
   strings like "أبرأهيم بن هأشم" that match no document ever written.
2. HadithService.extract_sanad returns narrators fully vocalized (tashkeel),
   but only ~14% of rijal documents carry any diacritics. A vocalized query
   like "مُحَمَّدُ بْنُ يَحْيَى" matched 0 of 12,937 documents; stripping
   diacritics and unifying letter variants makes it match the same 1,345
   documents its unvocalized form matches.

normalize_ar is therefore applied to BOTH the needle (the narrator name) and
the haystack (the corpus), so matching happens in one consistent space. It
must never be sent to an LLM prompt in place of the original text -- only used
for lookup and cache keys.
"""

import re

# Harakat, tanwin, shadda, dagger alef, and tatweel (kashida).
_TASHKEEL = re.compile(
    "[" "ً-ْ" "ٓ-ٟ" "ٰ" "ـ" "]"
)

# Letter-variant unification. Order matters only in that each pattern is
# independent; a single str.translate table would be equivalent for the 1:1
# mappings but hamza-bearing alefs need this before we can also strip bare
# hamza below.
_ALEF_VARIANTS = re.compile("[أإآٱ]")  # أ إ آ ٱ
_YEH_VARIANTS = re.compile("[يىئ]")  # ي ى ئ
_KAF_VARIANTS = re.compile("[ك]")  # ك -> ک
_TEH_MARBUTA = re.compile("[ة]")  # ة -> ه
_WAW_HAMZA = re.compile("[ؤ]")  # ؤ -> و
_BARE_HAMZA = re.compile("[ء]")  # ء -> (removed)

_WHITESPACE = re.compile(r"\s+")


def normalize_ar(text: str | None) -> str:
    """
    Fold diacritics and letter-shape variants so semantically identical
    narrator names collide in a substring search regardless of vocalization
    or Arabic/Persian orthography (ي vs ی, ك vs ک, أ/إ/آ vs ا).

    Idempotent: normalize_ar(normalize_ar(x)) == normalize_ar(x).
    """
    if not text:
        return ""

    result = _TASHKEEL.sub("", text)
    result = _ALEF_VARIANTS.sub("ا", result)  # -> ا
    result = _YEH_VARIANTS.sub("ی", result)  # -> ی (Persian yeh)
    result = _KAF_VARIANTS.sub("ک", result)  # -> ک (Persian keh)
    result = _TEH_MARBUTA.sub("ه", result)  # -> ه
    result = _WAW_HAMZA.sub("و", result)  # -> و
    result = _BARE_HAMZA.sub("", result)
    result = _WHITESPACE.sub(" ", result).strip()
    return result
