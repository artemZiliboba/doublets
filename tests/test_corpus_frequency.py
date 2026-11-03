import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from doublets.corpus_frequency import build_frequencies, export_frequencies
from doublets.dictionary_quality import read_frequencies


class FakeMorph:
    def parse(self, word):
        if word == "кота":
            return [SimpleNamespace(is_known=True, tag={"NOUN"}, normal_form="кот")]
        if word == "бежал":
            return [SimpleNamespace(is_known=True, tag={"VERB"}, normal_form="бежать")]
        return []


class CorpusFrequencyTests(unittest.TestCase):
    def test_exact_mode_and_yo(self):
        with TemporaryDirectory() as directory:
            corpus = Path(directory) / "corpus.txt"
            corpus.write_text("Кот кот, ёжик! Ежик. кота", encoding="utf-8")
            counts, report = build_frequencies(corpus, {"кот", "ёжик", "ежик"})
            self.assertEqual(dict(counts), {"кот": 2, "ёжик": 1, "ежик": 1})
            self.assertEqual(report["tokens"], 5)
            self.assertEqual(report["matched_tokens"], 4)
            output = Path(directory) / "frequency.txt"
            report_path = export_frequencies(counts, report, output)
            self.assertEqual(read_frequencies(output), {"кот": 2.0, "ёжик": 1.0, "ежик": 1.0})
            self.assertEqual(json.loads(report_path.read_text(encoding="utf-8"))["files"], 1)

    def test_lemma_mode_uses_preferred_noun_parse(self):
        with TemporaryDirectory() as directory:
            corpus = Path(directory) / "corpus.txt"
            corpus.write_text("Кота бежал кота", encoding="utf-8")
            counts, report = build_frequencies(corpus, {"кот"}, mode="lemma", morph=FakeMorph())
            self.assertEqual(dict(counts), {"кот": 2})
            self.assertEqual(report["matched_tokens"], 2)

    def test_directory_order_and_empty_files(self):
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "b.txt").write_text("кот", encoding="utf-8")
            (folder / "a.txt").write_text("", encoding="utf-8")
            first, report = build_frequencies(folder, {"кот"})
            second, again = build_frequencies(folder, {"кот"})
            self.assertEqual(first, second)
            self.assertEqual(report["corpus_sha256"], again["corpus_sha256"])
            self.assertEqual(report["files"], 2)

    def test_missing_directory_and_wrong_mode(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                build_frequencies(directory, {"кот"})
            path = Path(directory) / "corpus.txt"
            path.write_text("кот", encoding="utf-8")
            with self.assertRaises(ValueError):
                build_frequencies(path, {"кот"}, mode="invalid")


if __name__ == "__main__":
    unittest.main()
