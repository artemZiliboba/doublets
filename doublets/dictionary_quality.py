"""Local word-list quality tools for the Doublets game.

No remote downloads: frequency lists and exclusions are supplied by the user.
The core list is a subset of accepted known nouns; frequency is advisory,
not evidence that a token is a noun.
"""
from collections import Counter
from pathlib import Path
import hashlib
import json

from .engine import WordGraph

def load_words(path):
    """Read legacy JSON arrays and versioned {"words": [...]} exports."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("words")
    if not isinstance(data, list) or any(not isinstance(w, str) for w in data):
        raise ValueError("Expected a JSON list of words or an object with a 'words' list")
    return sorted(WordGraph(data).words)

def read_exclusions(path):
    if path is None:
        return set()
    return {
        line.strip().lower()
        for line in Path(path).read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

def read_frequencies(path):
    """Accept UTF-8 text 'word count', separated by space/tab or semicolon.

    Files with other source-specific formats must be converted beforehand.
    """
    if path is None:
        return {}
    counts = {}
    for number, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.replace(";", " ").split()
        if len(parts) != 2:
            raise ValueError(f"Bad frequency row {number}: expected 'word count'")
        word, raw = parts
        try:
            count = float(raw)
        except ValueError as exc:
            raise ValueError(f"Bad frequency at row {number}: {raw}") from exc
        if not (0 <= count < float("inf")):
            raise ValueError(f"Frequency must be finite and non-negative at row {number}")
        counts[word.lower()] = counts.get(word.lower(), 0) + count
    return counts

def component_stats(words):
    graph = WordGraph(words)
    components = []
    visited = set()
    isolated = 0
    edges = 0
    for word in sorted(graph.words):
        nbrs = graph.neighbors(word)
        edges += len(nbrs)
        isolated += not bool(nbrs)
        if word in visited:
            continue
        pending = [word]
        visited.add(word)
        size = 0
        while pending:
            current = pending.pop()
            size += 1
            for neighbor in graph.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    pending.append(neighbor)
        components.append(size)
    return {
        "words": len(graph.words),
        "edges": edges // 2,
        "isolated": isolated,
        "components": len(components),
        "largest_component": max(components, default=0),
    }

def analyze_lengths(words):
    return {str(n): component_stats(w for w in words if len(w) == n) for n in range(3, 7)}

def prepare_quality(words, exclusions=(), frequencies=None, min_frequency=0):
    if min_frequency < 0:
        raise ValueError("min_frequency must be >= 0")
    original = set(WordGraph(words).words)
    excluded = {w.lower() for w in exclusions}
    extended = sorted(original - excluded)
    if frequencies is None:
        core = []  # No frequency evidence: avoid claiming a curated core.
    else:
        core = sorted(w for w in extended if frequencies.get(w, 0) >= min_frequency and w in frequencies)
    return {
        "extended": extended,
        "core": core,
        "excluded": sorted(original & excluded),
    }

def write_quality_exports(result, output_dir, frequency_source=None):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in ("core", "extended", "excluded"):
        (output_dir / f"words_{name}.json").write_text(
            json.dumps(result[name], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    report = {
        "note": "Frequency filtering is a heuristic; manual editorial review is required.",
        "frequency_source": str(frequency_source) if frequency_source else None,
        "counts": {name: len(result[name]) for name in ("core", "extended", "excluded")},
        "core_by_length": analyze_lengths(result["core"]),
        "extended_by_length": analyze_lengths(result["extended"]),
        "extended_sha256": hashlib.sha256(
            json.dumps(result["extended"], ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }
    (output_dir / "quality_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report
