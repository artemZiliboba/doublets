import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from doublets.level_batches import pair_key, prepare_batch, read_decisions


class LevelBatchTests(unittest.TestCase):
    def test_pair_is_direction_independent(self):
        self.assertEqual(pair_key("кот", "год"), pair_key("год", "кот"))

    def test_registry_schema(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "decisions.json"
            self.assertEqual(read_decisions(path)["rejected"], [])
            path.write_text('{"version":2,"rejected":[],"deferred":[]}', encoding="utf-8")
            with self.assertRaises(ValueError):
                read_decisions(path)

    def test_batches_skip_previous_and_approved_pairs(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            core = root / "core.json"
            extended = root / "extended.json"
            approved = root / "approved.json"
            directory = root / "candidates"
            directory.mkdir()
            words = ["кот", "код", "год", "год", "род", "рот", "бот", "бок"]
            core.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
            extended.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
            approved.write_text(json.dumps({"version": 1, "levels": [
                {"id": "one", "start": "год", "end": "кот",
                 "min_moves": 2, "solution": ["год", "код", "кот"]}
            ]}, ensure_ascii=False), encoding="utf-8")
            kwargs = dict(core=core, extended=extended, approved=approved,
                          directory=directory, decisions=root / "missing.json",
                          frequency=root / "missing.txt", exclude=root / "missing-exclusions.txt",
                          min_moves=2, max_moves=3, candidate_limit=100, count=1)
            first = prepare_batch(batch_id="batch-001", **kwargs)
            self.assertEqual(first["generated"], 1)
            first_level = json.loads((directory / "batch-001.json").read_text(encoding="utf-8"))["levels"][0]
            self.assertNotEqual(pair_key(first_level["start"], first_level["end"]), pair_key("год", "кот"))
            with self.assertRaises(FileExistsError):
                prepare_batch(batch_id="batch-001", **kwargs)
            second = prepare_batch(batch_id="batch-002", **kwargs)
            self.assertEqual(second["generated"], 1)
            second_level = json.loads((directory / "batch-002.json").read_text(encoding="utf-8"))["levels"][0]
            self.assertNotEqual(pair_key(first_level["start"], first_level["end"]),
                                pair_key(second_level["start"], second_level["end"]))

    def test_invalid_batch_id(self):
        with self.assertRaises(ValueError):
            prepare_batch(batch_id="../bad")


if __name__ == "__main__":
    unittest.main()
