"""Deterministic level generation with curated endpoints and validated paths."""
from collections import Counter, defaultdict
import random

from .engine import WordGraph


def preferred_shortest_path(graph, start, end, familiar, frequencies):
    """Shortest path, preferring familiar and frequent intermediate words.

    Dynamic programming on BFS layers preserves the shortest-path guarantee.
    """
    distances = graph.distances(start)
    if end not in distances:
        return None
    depth = distances[end]
    best = {start: (0, 0.0, (start,))}
    for distance in range(depth):
        layer = sorted(w for w in best if distances[w] == distance)
        for word in layer:
            rare, negative_freq, path = best[word]
            for nxt in graph.neighbors(word):
                if distances.get(nxt) != distance + 1:
                    continue
                is_intermediate = nxt != end
                candidate = (
                    rare + int(is_intermediate and nxt not in familiar),
                    negative_freq - (frequencies.get(nxt, 0) if is_intermediate else 0),
                    path + (nxt,),
                )
                if nxt not in best or candidate < best[nxt]:
                    best[nxt] = candidate
    return list(best[end][2])


def generate_levels(core_words, extended_words, *, count=10, min_moves=2,
                    max_moves=6, seed=None, exclusions=(), frequencies=None,
                    min_length=3, max_length=4, max_unfamiliar=1,
                    candidate_limit=500):
    """Generate levels with core endpoints and shortest extended-only paths."""
    if (count < 0 or min_moves < 1 or max_moves < min_moves
            or not 3 <= min_length <= max_length <= 6
            or max_unfamiliar < 0 or candidate_limit < 1):
        raise ValueError("Require count >= 0, 1 <= min_moves <= max_moves, and 3 <= min_length <= max_length <= 6")
    excluded = {w.strip().lower() for w in exclusions}
    graph = WordGraph(w for w in extended_words if w.strip().lower() not in excluded
                      and min_length <= len(w.strip()) <= max_length)
    core = sorted(WordGraph(w for w in core_words if w.strip().lower() not in excluded
                            and min_length <= len(w.strip()) <= max_length).words)
    if not set(core) <= graph.words:
        raise ValueError("Core words must be a subset of extended words")
    if count == 0:
        return []
    frequencies = frequencies or {}
    familiar = set(core)
    by_length = defaultdict(list)
    for word in core:
        by_length[len(word)].append(word)
    rng = random.Random(seed)
    starts = core[:]
    rng.shuffle(starts)
    candidates = []
    for start in starts:
        distances = graph.distances(start, max_depth=max_moves)
        for end in by_length[len(start)]:
            if end > start and min_moves <= distances.get(end, -1) <= max_moves:
                candidates.append((start, end, distances[end]))
    rng.shuffle(candidates)
    ranked = []
    for start, end, distance in candidates[:candidate_limit]:
        path = preferred_shortest_path(graph, start, end, familiar, frequencies)
        rare_words = [w for w in path[1:-1] if w not in familiar]
        if len(rare_words) > max_unfamiliar:
            continue
        level = {
            "start": start, "end": end, "min_moves": distance,
            "solution": path,
            "quality": {
                "unfamiliar_intermediate_count": len(rare_words),
                "unfamiliar_intermediate_words": rare_words,
                "intermediate_frequency_sum": sum(frequencies.get(w, 0) for w in path[1:-1]),
            },
        }
        # Prefer no unfamiliar intermediates, then familiar endpoints and
        # frequent intermediate words. Randomness only breaks score ties.
        endpoint_frequency = min(frequencies.get(start, 0), frequencies.get(end, 0))
        score = (len(rare_words), -endpoint_frequency,
                 -level["quality"]["intermediate_frequency_sum"])
        ranked.append((score, rng.random(), level))
    ranked.sort(key=lambda item: (item[0], item[1]))
    return [level for _, _, level in ranked[:count]]


def summarize_levels(levels):
    unfamiliar = Counter(w for level in levels
                         for w in level["quality"]["unfamiliar_intermediate_words"])
    return {
        "generated": len(levels),
        "levels_with_unfamiliar_intermediates": sum(
            bool(level["quality"]["unfamiliar_intermediate_count"]) for level in levels
        ),
        "unfamiliar_intermediate_words": dict(sorted(unfamiliar.items())),
        "note": "Unfamiliar means absent from core, not necessarily invalid. Review all words manually.",
    }
