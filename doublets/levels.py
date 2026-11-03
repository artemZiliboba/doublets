"""Deterministic level generation with familiar endpoints and wider valid moves."""
from collections import defaultdict
import random

from .engine import WordGraph


def generate_levels(core_words, extended_words, *, count=10, min_moves=2,
                    max_moves=6, seed=None):
    """Generate distinct endpoint pairs with shortest paths in extended graph.

    Returns at most count levels. Only core words may be endpoints; every
    intermediate word is in extended. Shortest paths are computed in extended.
    """
    if count < 0 or min_moves < 1 or max_moves < min_moves:
        raise ValueError("Require count >= 0 and 1 <= min_moves <= max_moves")
    graph = WordGraph(extended_words)
    core = sorted(WordGraph(core_words).words)
    if not set(core) <= graph.words:
        raise ValueError("Core words must be a subset of extended words")
    if count == 0:
        return []
    by_length = defaultdict(list)
    for word in core:
        by_length[len(word)].append(word)
    rng = random.Random(seed)
    starts = core[:]
    rng.shuffle(starts)
    candidates = []
    for start in starts:
        distances = graph.distances(start, max_depth=max_moves)
        ends = [word for word in by_length[len(start)]
                if word > start and min_moves <= distances.get(word, -1) <= max_moves]
        # Only one orientation per pair; no duplicate reversed levels.
        for end in ends:
            candidates.append((start, end, distances[end]))
    rng.shuffle(candidates)
    levels = []
    for start, end, distance in candidates[:count]:
        path = graph.shortest_path(start, end)
        levels.append({
            "start": start, "end": end, "min_moves": distance,
            "solution": path,
        })
    return levels
