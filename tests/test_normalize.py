"""
Guards the two real bugs that motivated core/text_normalize.py:
  - vocalized narrator names matched 0 documents against an unvocalized corpus
  - the old "ar" direction replaced EVERY alef, corrupting names like
    "ابراهيم بن هاشم" into "أبرأهيم بن هأشم"
"""

import random

from core.text_normalize import normalize_ar


def test_vocalized_matches_unvocalized():
    vocalized = "مُحَمَّدُ بْنُ يَحْيَى"
    unvocalized = "محمد بن يحيى"
    assert normalize_ar(vocalized) == normalize_ar(unvocalized)


def test_medial_alef_is_not_corrupted():
    # The old .replace("ا", "أ") would have turned this into "أبرأهيم بن هأشم".
    result = normalize_ar("ابراهيم بن هاشم")
    assert "أ" not in result
    assert result == "ابراهیم بن هاشم"


def test_yeh_and_kaf_variants_unify():
    assert normalize_ar("علي") == normalize_ar("علی")
    assert normalize_ar("ك") == normalize_ar("ک")


def test_empty_and_none_are_safe():
    assert normalize_ar("") == ""
    assert normalize_ar(None) == ""


def test_idempotent_over_random_arabic_strings():
    alphabet = "ابتثجحخدذرزسشصضطظعغفقكلمنهوىيءأإآؤئةًٌٍَُِّْـ "
    rng = random.Random(0)
    for _ in range(500):
        s = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 20)))
        once = normalize_ar(s)
        twice = normalize_ar(once)
        assert once == twice, f"not idempotent for {s!r}: {once!r} != {twice!r}"
