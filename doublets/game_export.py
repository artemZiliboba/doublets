"""Export a validated, self-contained JSON bundle for the browser game."""
import hashlib
import json
from pathlib import Path

from .approved_levels import load_approved_levels, validate_approved_levels
from .dictionary_quality import load_words, read_exclusions


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def export_game(*, levels="data/levels_approved.json",
                words="data/processed/words_extended.json",
                exclude="data/quality/excluded_words.txt",
                out_dir="game-data"):
    """Validate all levels before exporting; never publish invalid game data."""
    approved = load_approved_levels(levels)
    vocabulary = load_words(words)
    exclusions = read_exclusions(exclude) if Path(exclude).exists() else set()
    allowed = sorted(set(vocabulary) - exclusions)
    errors = validate_approved_levels(approved, allowed)
    if errors:
        raise ValueError("Approved levels failed validation:\n" + "\n".join(errors))

    # Preserve level IDs/order; publish only fields needed by the game.
    public_levels = [
        {key: level[key] for key in ("id", "start", "end", "min_moves", "solution")}
        for level in approved
    ]
    levels_data = {"version": 1, "levels": public_levels}
    words_data = {"version": 1, "words": allowed}
    payloads = {
        "levels.json": _json_bytes(levels_data),
        "words.json": _json_bytes(words_data),
    }
    manifest = {
        "version": 1,
        "rules": {
            "language": "ru",
            "min_word_length": 3,
            "max_word_length": 6,
            "one_letter_per_move": True,
            "yo_distinct": True,
        },
        "level_count": len(public_levels),
        "word_count": len(allowed),
        "files": {
            name: {"sha256": hashlib.sha256(content).hexdigest()}
            for name, content in payloads.items()
        },
    }
    payloads["manifest.json"] = _json_bytes(manifest)
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    for name, content in payloads.items():
        (target / name).write_bytes(content)
    return {"output": str(target), "levels": len(public_levels),
            "words": len(allowed), "files": list(payloads)}
