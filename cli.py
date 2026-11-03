import argparse
import json
from pathlib import Path
from doublets import WordGraph, extract_nouns
from doublets.dictionary import export_words

p = argparse.ArgumentParser()
sub = p.add_subparsers(dest='command', required=True)
b = sub.add_parser('build'); b.add_argument('xml'); b.add_argument('--out', default='data/export/words.json')
for name in ('solve', 'generate', 'stats'):
    q = sub.add_parser(name)
    q.add_argument('--words', default='data/export/words.json')
    if name == 'solve': q.add_argument('start'); q.add_argument('end')
    if name == 'generate': q.add_argument('--min-moves', type=int, default=2); q.add_argument('--max-moves', type=int, default=6); q.add_argument('--seed', type=int)
a = p.parse_args()
if a.command == 'build':
    words = extract_nouns(a.xml); export_words(words, a.out); print(f'Exported {len(words)} words to {a.out}')
else:
    words = json.loads(Path(a.words).read_text(encoding='utf-8'))['words']
    graph = WordGraph(words)
    if a.command == 'solve': print(json.dumps(graph.shortest_path(a.start, a.end), ensure_ascii=False))
    if a.command == 'generate': print(json.dumps(graph.random_level(a.min_moves, a.max_moves, a.seed), ensure_ascii=False))
    if a.command == 'stats':
        from collections import Counter
        print(json.dumps({'words': len(graph.words), 'by_length': dict(sorted(Counter(map(len, graph.words)).items())), 'isolated': sum(not graph.neighbors(w) for w in graph.words)}, ensure_ascii=False, indent=2))
