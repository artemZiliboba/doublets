"""Import a local FrequencyWords-style UTF-8 'word count' file.

Source is never downloaded or committed by this tool. Input counts represent
word forms, not necessarily noun lemmas. Optional lemmatization is heuristic.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

from .corpus_frequency import export_frequencies
from .dictionary_quality import load_words


def import_frequency_file(source, words, mode="lemma"):
    if mode not in ("exact", "lemma"):
        raise ValueError("mode must be exact or lemma")
    source = Path(source)
    raw = source.read_bytes()
    morph = None
    if mode == "lemma":
        import pymorphy3
        morph = pymorphy3.MorphAnalyzer()
    allowed = set(words)
    counts = Counter()
    seen = 0
    accepted = 0
    for lineno, line in enumerate(raw.decode("utf-8-sig").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 2:
            raise ValueError(f"Line {lineno}: expected word and integer count")
        word, number = parts
        try:
            count = int(number)
        except ValueError as exc:
            raise ValueError(f"Line {lineno}: invalid integer count") from exc
        if count < 0:
            raise ValueError(f"Line {lineno}: count must be nonnegative")
        seen += 1
        word = word.lower()
        if word not in allowed and mode == "lemma":
            parses = morph.parse(word)
            best = parses[0] if parses else None
            if best is None or not best.is_known or "NOUN" not in best.tag:
                continue
            word = best.normal_form
        if word in allowed:
            counts[word] += count
            accepted += 1
    report = {
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "mode": mode,
        "source_rows": seen,
        "matched_rows": accepted,
        "matched_lemmas": len(counts),
        "matched_occurrences": sum(counts.values()),
        "note": "FrequencyWords is subtitle-based. Lemma mode is heuristic and may misclassify homonyms.",
    }
    return counts, report


def write_import(counts, report, output):
    return export_frequencies(counts, report, output)
