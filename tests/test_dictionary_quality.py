import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from doublets.dictionary_quality import (
    analyze_lengths,
    load_words,
    prepare_quality,
    read_exclusions,
    read_frequencies,
    write_quality_exports,
)


class DictionaryQualityTests(unittest.TestCase):
    def test_legacy_and_versioned_exports(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "words.json"
            for data in (["кот", "кит", "ёжик"], {"words": ["кот", "кит", "ёжик"]}):
                path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                self.assertEqual(load_words(path), ["ёжик", "кит", "кот"])

    def test_invalid_export(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "words.json"
            path.write_text('{"other":[]}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_words(path)

    def test_frequencies_and_exclusions(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "freq.txt"
            path.write_text("# sample\nкот 10\nкит;3\nкот 2\n", encoding="utf-8")
            self.assertEqual(read_frequencies(path), {"кот": 12, "кит": 3})
            excludes = Path(folder) / "exclude.txt"
            excludes.write_text("# note\nКИТ\n\n", encoding="utf-8")
            self.assertEqual(read_exclusions(excludes), {"кит"})

    def test_core_requires_frequency_source(self):
        words = ["кот", "кит", "бит", "дом"]
        result = prepare_quality(words, exclusions={"дом"})
        self.assertEqual(result["core"], [])
        self.assertEqual(result["extended"], ["бит", "кит", "кот"])
        self.assertEqual(result["excluded"], ["дом"])

    def test_core_subset_and_yo(self):
        result = prepare_quality(
            ["ёжик", "ежик", "кот", "кит"],
            frequencies={"ёжик": 8, "ежик": 0, "кот": 4, "кит": 1},
            min_frequency=3,
        )
        self.assertEqual(result["core"], ["ёжик", "кот"])
        self.assertIn("ежик", result["extended"])
        self.assertIn("ёжик", result["extended"])

    def test_graph_component_statistics(self):
        result = analyze_lengths(["кот", "кит", "бит", "дом"])
        self.assertEqual(result["3"]["largest_component"], 3)
        self.assertEqual(result["3"]["isolated"], 1)
        self.assertEqual(result["3"]["edges"], 2)

    def test_writes_outputs(self):
        with TemporaryDirectory() as folder:
            result = prepare_quality(["кот", "кит", "дом"], frequencies={"кот": 2}, min_frequency=1)
            report = write_quality_exports(result, folder, "fixture.txt")
            self.assertEqual(report["counts"]["core"], 1)
            self.assertEqual(
                json.loads((Path(folder) / "words_core.json").read_text(encoding="utf-8")),
                ["кот"],
            )


if __name__ == "__main__":
    unittest.main()
