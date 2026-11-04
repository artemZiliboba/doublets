import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from doublets.game_export import export_game


class GameExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.levels = self.root / "levels.json"
        self.words = self.root / "words.json"
        self.exclude = self.root / "excluded.txt"
        self.out = self.root / "game-data"
        self.levels.write_text(json.dumps({
            "version": 1,
            "levels": [{"id": "level-001", "start": "год", "end": "кот",
                        "min_moves": 2, "solution": ["год", "код", "кот"]}],
        }, ensure_ascii=False), encoding="utf-8")
        self.words.write_text(json.dumps(["год", "код", "кот", "шум"], ensure_ascii=False),
                              encoding="utf-8")
        self.exclude.write_text("шум\n", encoding="utf-8")

    def run_export(self):
        return export_game(levels=self.levels, words=self.words,
                           exclude=self.exclude, out_dir=self.out)

    def test_exports_validated_bundle_with_hashes(self):
        result = self.run_export()
        self.assertEqual(result["levels"], 1)
        self.assertEqual(result["words"], 3)
        levels = json.loads((self.out / "levels.json").read_text(encoding="utf-8"))
        words = json.loads((self.out / "words.json").read_text(encoding="utf-8"))
        manifest = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(levels["levels"][0]["id"], "level-001")
        self.assertEqual(words["words"], ["год", "код", "кот"])
        self.assertEqual(manifest["level_count"], 1)
        self.assertTrue(manifest["rules"]["yo_distinct"])
        for name in ("levels.json", "words.json"):
            digest = hashlib.sha256((self.out / name).read_bytes()).hexdigest()
            self.assertEqual(manifest["files"][name]["sha256"], digest)

    def test_rejects_invalid_level_without_writing_bundle(self):
        data = json.loads(self.levels.read_text(encoding="utf-8"))
        data["levels"][0]["min_moves"] = 3
        self.levels.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "validation"):
            self.run_export()
        self.assertFalse(self.out.exists())

    def test_rejects_excluded_solution_word(self):
        self.exclude.write_text("код\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.run_export()
        self.assertFalse(self.out.exists())

    def test_export_is_deterministic(self):
        self.run_export()
        before = [(self.out / name).read_bytes()
                  for name in ("levels.json", "words.json", "manifest.json")]
        self.run_export()
        after = [(self.out / name).read_bytes()
                 for name in ("levels.json", "words.json", "manifest.json")]
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
