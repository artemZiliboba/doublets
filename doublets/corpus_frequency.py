"""Build a reproducible word-frequency file from user-provided UTF-8 text.

No external corpus is downloaded. Default mode counts exact dictionary
spellings; optional lemma mode uses the highest-ranked known NOUN analysis
and is therefore heuristic for ambiguous word forms.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from .dictionary_quality import load_words

TOKEN = re.compile(r"[а-яё]+", re.IGNORECASE)


def text_files(source):
    source = Path(source)
    if source.is_file():
        if source.suffix.lower() != ".txt":
            raise ValueError("Expected a .txt file")
        return [source]
    if not source.is_dir():
        raise FileNotFoundError(source)
    files = sorted(p for p in source.rglob("*.txt") if p.is_file())
    if not files:
        raise ValueError(f"No .txt files found in {source}")
    return files


def build_frequencies(source, dictionary, mode="exact", morph=None):
    if mode not in ("exact", "lemma"):
        raise ValueError("mode must be 'exact' or 'lemma'")
    allowed = set(dictionary)
    if mode == "lemma" and morph is None:
        import pymorphy3
        morph = pymorphy3.MorphAnalyzer()

    counts = Counter()
    total_tokens = 0
    matched_tokens = 0
    files = text_files(source)
    digest = hashlib.sha256()
    for file in files:
        data = file.read_bytes()
        # Incorporate paths relative to corpus root and contents, not absolute paths.
        relative = file.name if Path(source).is_file() else file.relative_to(source).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\\0")
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
        text = data.decode("utf-8-sig")
        for match in TOKEN.finditer(text):
            token = match.group().lower()
            total_tokens += 1
            word = token
            if mode == "lemma" and token not in allowed:
                # One preferred analysis, not all hypothetical noun analyses:
                # this avoids counting every ambiguous verb/adjective as a noun.
                parses = morph.parse(token)
                best = parses[0] if parses else None
                if best is None or not best.is_known or "NOUN" not in best.tag:
                    continue
                word = best.normal_form
            if word in allowed:
                counts[word] += 1
                matched_tokens += 1

    return counts, {
        "mode": mode,
        "files": len(files),
        "tokens": total_tokens,
        "matched_tokens": matched_tokens,
        "matched_ratio": round(matched_tokens / total_tokens, 6) if total_tokens else 0,
        "matched_unique_words": len(counts),
        "corpus_sha256": digest.hexdigest(),
        "note": (
            "Counts reflect this corpus, not general Russian usage. "
            "Lemma mode uses only the highest-ranked morphological analysis."
        ),
    }


def export_frequencies(counts, report, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(f"{word} {counts[word]}\\n" for word in sorted(counts)),
        encoding="utf-8",
    )
    report_path = output.with_suffix(".report.json")
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\\n",
        encoding="utf-8",
    )
    return report_path
