"""Command line entry point for the Doublets dictionary and engine."""
import argparse
import json
from collections import Counter
from pathlib import Path

from doublets import WordGraph, extract_nouns
from doublets.dictionary import export_words
from doublets.dictionary_quality import (
    analyze_lengths, load_words, prepare_quality, read_exclusions,
    read_frequencies, write_quality_exports,
)


def main(argv=None):
    p = argparse.ArgumentParser(description="Russian Doublets word tools")
    sub = p.add_subparsers(dest="command", required=True)

    b = sub.add_parser("build", help="Build from OpenCorpora XML")
    b.add_argument("xml")
    b.add_argument("--out", default="data/export/words.json")

    bp = sub.add_parser("build-pymorphy", help="Build using installed pymorphy3 dictionaries")
    bp.add_argument("--out", default="data/export/words.json")

    for name in ("solve", "generate", "stats", "analyze", "quality"):
        q = sub.add_parser(name)
        q.add_argument("--words", default="data/export/words.json")
        if name == "solve":
            q.add_argument("start")
            q.add_argument("end")
        if name == "generate":
            q.add_argument("--min-moves", type=int, default=2)
            q.add_argument("--max-moves", type=int, default=6)
            q.add_argument("--seed", type=int)
        if name == "quality":
            q.add_argument("--exclude", default="data/quality/excluded_words.txt")
            q.add_argument("--frequency", default=None)
            q.add_argument("--min-frequency", type=float, default=1)
            q.add_argument("--out-dir", default="data/processed")

    cf = sub.add_parser("corpus-frequency", help="Count words in a local UTF-8 text corpus")
    cf.add_argument("source", help="A .txt file or directory containing .txt files")
    cf.add_argument("--words", default="data/export/words.json")
    cf.add_argument("--out", default="data/quality/frequency_ru.txt")
    cf.add_argument("--mode", choices=("exact", "lemma"), default="exact")

    fi = sub.add_parser("import-frequency", help="Import local FrequencyWords-style word counts")
    fi.add_argument("source", help="UTF-8 file with 'word count' per line")
    fi.add_argument("--words", default="data/export/words.json")
    fi.add_argument("--out", default="data/quality/frequency_ru.txt")
    fi.add_argument("--mode", choices=("exact", "lemma"), default="lemma")

    levels = sub.add_parser("generate-levels", help="Generate levels with core endpoints and extended paths")
    levels.add_argument("--core", default="data/processed/words_core.json")
    levels.add_argument("--extended", default="data/processed/words_extended.json")
    levels.add_argument("--count", type=int, default=10)
    levels.add_argument("--min-moves", type=int, default=2)
    levels.add_argument("--max-moves", type=int, default=6)
    levels.add_argument("--seed", type=int, default=42)
    levels.add_argument("--out", default="data/processed/levels.json")
    levels.add_argument("--report", default="data/processed/levels_report.json")
    levels.add_argument("--exclude", default="data/quality/excluded_words.txt")
    levels.add_argument("--frequency", default="data/quality/frequency_ru.txt")
    levels.add_argument("--min-length", type=int, default=3)
    levels.add_argument("--max-length", type=int, default=4)
    levels.add_argument("--max-unfamiliar", type=int, default=1)
    levels.add_argument("--candidate-limit", type=int, default=500)

    args = p.parse_args(argv)
    if args.command == "build":
        words = extract_nouns(args.xml)
        export_words(words, args.out)
        print(f"Exported {len(words)} words to {args.out}")
        return

    if args.command == "build-pymorphy":
        from build_pymorphy_dictionary import build_dictionary
        build_dictionary(args.out)
        return

    if args.command == "import-frequency":
        from doublets.frequency_import import import_frequency_file, write_import
        words = load_words(args.words)
        counts, report = import_frequency_file(args.source, words, mode=args.mode)
        report_path = write_import(counts, report, args.out)
        print(json.dumps({"frequency_file": args.out, "report_file": str(report_path), **report}, ensure_ascii=False, indent=2))
        return

    if args.command == "generate-levels":
        from doublets.levels import generate_levels, summarize_levels
        exclusions = read_exclusions(args.exclude) if Path(args.exclude).exists() else set()
        frequencies = read_frequencies(args.frequency) if Path(args.frequency).exists() else {}
        levels_data = generate_levels(
            load_words(args.core), load_words(args.extended),
            count=args.count, min_moves=args.min_moves,
            max_moves=args.max_moves, seed=args.seed,
            exclusions=exclusions, frequencies=frequencies,
            min_length=args.min_length, max_length=args.max_length,
            max_unfamiliar=args.max_unfamiliar,
            candidate_limit=args.candidate_limit,
        )
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(levels_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report = summarize_levels(levels_data)
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"output": str(output), "report": str(report_path),
                          "requested": args.count, **report, "levels": levels_data},
                         ensure_ascii=False, indent=2))
        return

    if args.command == "corpus-frequency":
        from doublets.corpus_frequency import build_frequencies, export_frequencies
        words = load_words(args.words)
        counts, report = build_frequencies(args.source, words, mode=args.mode)
        report_path = export_frequencies(counts, report, args.out)
        print(json.dumps({"frequency_file": args.out, "report_file": str(report_path), **report}, ensure_ascii=False, indent=2))
        return

    words = load_words(args.words)
    if args.command == "quality":
        exclusions = read_exclusions(args.exclude) if Path(args.exclude).exists() else set()
        freq = read_frequencies(args.frequency)
        result = prepare_quality(
            words,
            exclusions=exclusions,
            frequencies=freq if args.frequency is not None else None,
            min_frequency=args.min_frequency,
        )
        report = write_quality_exports(result, args.out_dir, args.frequency)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    if args.command == "analyze":
        print(json.dumps(analyze_lengths(words), ensure_ascii=False, indent=2))
        return

    graph = WordGraph(words)
    if args.command == "solve":
        output = graph.shortest_path(args.start, args.end)
    elif args.command == "generate":
        if args.min_moves < 0 or args.max_moves < args.min_moves:
            p.error("Require 0 <= --min-moves <= --max-moves")
        output = graph.random_level(args.min_moves, args.max_moves, args.seed)
    else:
        output = {
            "words": len(graph.words),
            "by_length": dict(sorted(Counter(map(len, graph.words)).items())),
            "isolated": sum(not graph.neighbors(w) for w in graph.words),
        }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
