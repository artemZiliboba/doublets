"""Prepare self-contained candidate batches for asynchronous editorial review."""
import json
from pathlib import Path

from .approved_levels import load_approved_levels
from .dictionary_quality import load_words, read_exclusions, read_frequencies
from .levels import generate_levels, summarize_levels


def pair_key(start, end):
    return tuple(sorted((start, end)))


def read_decisions(path):
    path = Path(path)
    if not path.exists():
        return {"version": 1, "rejected": [], "deferred": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("Invalid decisions registry version")
    for name in ("rejected", "deferred"):
        if not isinstance(data.get(name), list):
            raise ValueError(f"Decisions registry needs {name} list")
        for entry in data[name]:
            if (not isinstance(entry, dict)
                    or not all(isinstance(entry.get(k), str) for k in ("start", "end", "reason"))):
                raise ValueError(f"Invalid {name} entry")
    return data


def prepare_batch(*, batch_id, count=40, seed=42, min_moves=2, max_moves=5,
                  candidate_limit=2000, max_unfamiliar=1,
                  core="data/processed/words_core.json",
                  extended="data/processed/words_extended.json",
                  frequency="data/quality/frequency_ru.txt",
                  exclude="data/quality/excluded_words.txt",
                  approved="data/levels_approved.json",
                  decisions="data/quality/level_decisions.json",
                  directory="data/candidates"):
    if not batch_id or not all(c.isascii() and (c.isalnum() or c in "-_") for c in batch_id):
        raise ValueError("batch-id must contain only ASCII letters, digits, '-' or '_'")
    if count < 1:
        raise ValueError("count must be positive")
    output = Path(directory) / f"{batch_id}.json"
    if output.exists():
        raise FileExistsError(f"Batch already exists: {output}")
    approved_levels = load_approved_levels(approved)
    registry = read_decisions(decisions)
    blocked = {pair_key(x["start"], x["end"]) for x in approved_levels}
    for status in ("rejected", "deferred"):
        blocked.update(pair_key(x["start"], x["end"]) for x in registry[status])
    # Include earlier batches, including pending review, to prevent repeat work.
    for existing in sorted(Path(directory).glob("*.json")):
        data = json.loads(existing.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("levels"), list):
            raise ValueError(f"Invalid candidate batch: {existing}")
        for level in data["levels"]:
            blocked.add(pair_key(level["start"], level["end"]))
    excluded = read_exclusions(exclude) if Path(exclude).exists() else set()
    frequencies = read_frequencies(frequency) if Path(frequency).exists() else {}
    # Ranking must happen after processed pairs are removed, so there is no
    # silent shortage when the highest-ranked candidates were already reviewed.
    levels = generate_levels(
        load_words(core), load_words(extended), count=count,
        min_moves=min_moves, max_moves=max_moves, seed=seed,
        exclusions=excluded, frequencies=frequencies,
        max_unfamiliar=max_unfamiliar, candidate_limit=candidate_limit,
        excluded_pairs=blocked,
    )
    if len(levels) < count:
        raise ValueError(f"Only {len(levels)} fresh candidates found; requested {count}. "
                         "Try a higher --candidate-limit or a different seed.")
    payload = {
        "version": 1, "batch_id": batch_id, "status": "pending",
        "parameters": {"seed": seed, "min_moves": min_moves,
                       "max_moves": max_moves, "max_unfamiliar": max_unfamiliar,
                       "candidate_limit": candidate_limit},
        "levels": levels,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation avoids accidentally overwriting an existing review batch.
    with output.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return {"output": str(output), "generated": len(levels),
            "previously_processed_pairs": len(blocked), **summarize_levels(levels)}
