import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from doublets.frequency_import import import_frequency_file, write_import
from doublets.dictionary_quality import read_frequencies


class FrequencyImportTests(unittest.TestCase):
    def test_exact_counts_and_yo(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "ru.txt"
            source.write_text("кот 10\nкит 5\nёжик 3\nкот 2\n", encoding="utf-8")
            counts, report = import_frequency_file(source, {"кот", "ёжик"}, mode="exact")
            self.assertEqual(dict(counts), {"кот": 12, "ёжик": 3})
            self.assertEqual(report["matched_rows"], 3)
            output = Path(folder) / "out.txt"
            write_import(counts, report, output)
            self.assertEqual(read_frequencies(output), {"кот": 12.0, "ёжик": 3.0})

    def test_invalid_input(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "ru.txt"
            for bad in ("кот abc", "кот -1", "кот 1.5", "кот"):
                source.write_text(bad, encoding="utf-8")
                with self.assertRaises(ValueError):
                    import_frequency_file(source, {"кот"}, mode="exact")

    def test_reject_invalid_mode(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "ru.txt"
            source.write_text("кот 2", encoding="utf-8")
            with self.assertRaises(ValueError):
                import_frequency_file(source, {"кот"}, mode="other")

    def test_lemma_mode_with_stub(self):
        from types import SimpleNamespace
        class Stub:
            def parse(self, word):
                if word == "кота":
                    return [SimpleNamespace(is_known=True, tag={"NOUN"}, normal_form="кот")]
                return []
        with TemporaryDirectory() as folder:
            source = Path(folder) / "ru.txt"
            source.write_text("кота 8\nкот 3\n", encoding="utf-8")
            with patch("pymorphy3.MorphAnalyzer", return_value=Stub()):
                counts, report = import_frequency_file(source, {"кот"}, mode="lemma")
            self.assertEqual(dict(counts), {"кот": 11})
            self.assertEqual(report["matched_lemmas"], 1)


if __name__ == "__main__":
    unittest.main()
