
import json
from collections import Counter, defaultdict, deque
from pathlib import Path

WORDS_PATH = (
    Path(__file__).resolve().parent
    / "data" / "export" / "words.json"
)


def build_graph(words):
    """Связывает слова, отличающиеся ровно одной буквой."""
    graph = {word: set() for word in words}
    patterns = defaultdict(list)

    for word in words:
        for i in range(len(word)):
            pattern = (len(word), i, word[:i] + "*" + word[i + 1:])
            patterns[pattern].append(word)

    for group in patterns.values():
        for i, word in enumerate(group):
            for other in group[i + 1:]:
                graph[word].add(other)
                graph[other].add(word)

    return graph


def connected_components(graph):
    """Находит все связные компоненты."""
    visited = set()
    components = []

    for start in graph:
        if start in visited:
            continue

        component = []
        queue = deque([start])
        visited.add(start)

        while queue:
            word = queue.popleft()
            component.append(word)

            for neighbor in graph[word]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        components.append(component)

    return sorted(components, key=len, reverse=True)


def shortest_path(graph, start, end):
    """Находит кратчайшую цепочку между двумя словами."""
    if start not in graph or end not in graph:
        return None

    queue = deque([start])
    parents = {start: None}

    while queue:
        word = queue.popleft()

        if word == end:
            path = []

            while word is not None:
                path.append(word)
                word = parents[word]

            return path[::-1]

        for neighbor in sorted(graph[word]):
            if neighbor not in parents:
                parents[neighbor] = word
                queue.append(neighbor)

    return None


def analyze(words):
    for length in range(3, 7):
        subset = sorted(w for w in words if len(w) == length)
        graph = build_graph(subset)
        components = connected_components(graph)

        isolated = sum(not neighbors for neighbors in graph.values())
        edges = sum(len(neighbors) for neighbors in graph.values()) // 2
        largest = components[0] if components else []

        print(f"\n{'=' * 45}")
        print(f"СЛОВА ДЛИНОЙ {length}")
        print(f"{'=' * 45}")
        print(f"Всего слов:             {len(subset)}")
        print(f"Связей:                 {edges}")
        print(f"Изолированных слов:     {isolated}")
        print(f"Связных компонентов:    {len(components)}")
        print(f"Крупнейшая компонента:  {len(largest)}")

        if subset:
            print(
                f"Доля крупнейшей:        "
                f"{len(largest) / len(subset):.1%}"
            )

        sizes = Counter(len(c) for c in components)
        print("Компоненты по размеру:", dict(sorted(sizes.items())))

        if largest:
            print("\nПримеры слов из крупнейшей компоненты:")
            print(", ".join(sorted(largest)[:20]))

            # Проверяем один воспроизводимый пример пути.
            start = min(largest)
            distances = {start: 0}
            queue = deque([start])

            while queue:
                current = queue.popleft()

                for neighbor in sorted(graph[current]):
                    if neighbor not in distances:
                        distances[neighbor] = distances[current] + 1
                        queue.append(neighbor)

            farthest = max(
                distances,
                key=lambda word: (distances[word], word),
            )

            path = shortest_path(graph, start, farthest)

            print("\nПример цепочки:")
            print(" -> ".join(path))
            print(f"Количество ходов: {len(path) - 1}")


if __name__ == "__main__":
    words = json.loads(WORDS_PATH.read_text(encoding="utf-8"))
    analyze(set(words))
