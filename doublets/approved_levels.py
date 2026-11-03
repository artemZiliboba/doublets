"""Versioned, human-approved levels; independent of candidate generation."""
import json
from pathlib import Path

from .engine import WordGraph, one_letter_apart


def load_approved_levels(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("levels"), list):
        raise ValueError("Expected {'version': 1, 'levels': [...]} ")
    return data["levels"]


def validate_approved_levels(levels, words, exclusions=()):
    """Return structured errors; never mutate or silently repair approved levels."""
    graph = WordGraph(words)
    excluded = {w.strip().lower() for w in exclusions}
    allowed = graph.words - excluded
    errors = []
    seen_ids = set()
    seen_pairs = set()
    if not isinstance(levels, list):
        return ["levels must be an array"]
    for index, level in enumerate(levels, 1):
        prefix = f"level #{index}"
        if not isinstance(level, dict):
            errors.append(f"{prefix}: expected object")
            continue
        identifier = level.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            errors.append(f"{prefix}: id must be nonempty string")
        elif identifier in seen_ids:
            errors.append(f"{prefix}: duplicate id {identifier}")
        else:
            seen_ids.add(identifier)
        start, end = level.get("start"), level.get("end")
        path = level.get("solution")
        moves = level.get("min_moves")
        if not isinstance(start, str) or not isinstance(end, str):
            errors.append(f"{prefix}: start/end must be strings")
            continue
        if start not in allowed or end not in allowed or start == end:
            errors.append(f"{prefix}: endpoints must be distinct allowed words")
            continue
        pair = tuple(sorted((start, end)))
        if pair in seen_pairs:
            errors.append(f"{prefix}: duplicate endpoint pair")
        seen_pairs.add(pair)
        if not isinstance(path, list) or len(path) < 2 or any(not isinstance(w, str) for w in path):
            errors.append(f"{prefix}: solution must be an array of at least two words")
            continue
        if path[0] != start or path[-1] != end:
            errors.append(f"{prefix}: solution endpoints mismatch")
        if any(w not in allowed for w in path):
            errors.append(f"{prefix}: solution contains unknown or excluded word")
        if len(path) != len(set(path)):
            errors.append(f"{prefix}: solution repeats a word")
        if any(not one_letter_apart(a, b) for a, b in zip(path, path[1:])):
            errors.append(f"{prefix}: solution contains invalid transition")
        shortest = graph.shortest_path(start, end)
        # An excluded word may create a shorter route in the unfiltered graph.
        # Rebuild the graph to ensure min_moves describes the actual game rules.
        if excluded:
            shortest = WordGraph(allowed).shortest_path(start, end)
        if type(moves) is not int or moves < 1 or shortest is None or moves != len(shortest) - 1:
            errors.append(f"{prefix}: min_moves does not match shortest allowed route")
        elif len(path) - 1 != moves:
            errors.append(f"{prefix}: solution is not a shortest route")
    return errors
