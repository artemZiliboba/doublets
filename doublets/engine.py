from collections import defaultdict, deque
from dataclasses import dataclass
import random


def normalize(word):
    return word.strip().lower()


def one_letter_apart(a, b):
    return len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1


class WordGraph:
    def __init__(self, words):
        self.words = {normalize(w) for w in words if 3 <= len(normalize(w)) <= 6 and normalize(w).isalpha() and all('а' <= c <= 'я' or c == 'ё' for c in normalize(w))}
        self.index = defaultdict(list)
        for word in sorted(self.words):
            for i in range(len(word)):
                self.index[(len(word), i, word[:i], word[i+1:])].append(word)

    def neighbors(self, word):
        word = normalize(word)
        result = set()
        for i in range(len(word)):
            result.update(self.index.get((len(word), i, word[:i], word[i+1:]), []))
        result.discard(word)
        return sorted(result)

    def distances(self, start, max_depth=None):
        start = normalize(start)
        if start not in self.words:
            raise ValueError('Unknown start word')
        dist = {start: 0}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            if max_depth is not None and dist[current] >= max_depth:
                continue
            for nxt in self.neighbors(current):
                if nxt not in dist:
                    dist[nxt] = dist[current] + 1
                    queue.append(nxt)
        return dist

    def shortest_path(self, start, end):
        start, end = normalize(start), normalize(end)
        if start not in self.words or end not in self.words or len(start) != len(end):
            return None
        parents = {start: None}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            if current == end:
                path = []
                while current is not None:
                    path.append(current)
                    current = parents[current]
                return path[::-1]
            for nxt in self.neighbors(current):
                if nxt not in parents:
                    parents[nxt] = current
                    queue.append(nxt)
        return None

    def validate_move(self, previous, candidate):
        candidate = normalize(candidate)
        return candidate in self.words and one_letter_apart(normalize(previous), candidate)

    def random_level(self, min_moves=2, max_moves=5, seed=None, attempts=100):
        rng = random.Random(seed)
        words = sorted(self.words)
        if not words:
            return None
        for _ in range(attempts):
            start = rng.choice(words)
            distances = self.distances(start, max_moves)
            candidates = [w for w, d in distances.items() if min_moves <= d <= max_moves]
            if candidates:
                end = rng.choice(sorted(candidates))
                return {'start': start, 'end': end, 'min_moves': distances[end]}
        return None
