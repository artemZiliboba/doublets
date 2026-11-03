import json
from pathlib import Path
import tempfile
import unittest

from doublets.approved_levels import load_approved_levels, validate_approved_levels


class ApprovedLevelTests(unittest.TestCase):
    def setUp(self):
        self.words = ["год", "код", "кот", "бог", "бок", "сок",
                      "боб", "рог", "род", "док", "бак", "бал", "зал",
                      "газ", "гад", "рот"]
        self.level = {"id": "level-001", "start": "год", "end": "кот",
                      "min_moves": 2, "solution": ["год", "код", "кот"]}

    def test_valid_level(self):
        self.assertEqual(validate_approved_levels([self.level], self.words), [])

    def test_rejects_duplicate_ids_and_pairs(self):
        other = dict(self.level, id="level-001")
        errors = validate_approved_levels([self.level, other], self.words)
        self.assertTrue(any("duplicate id" in e for e in errors))
        self.assertTrue(any("duplicate endpoint pair" in e for e in errors))

    def test_rejects_invalid_moves_and_exclusions(self):
        bad = dict(self.level, solution=["год", "кот"])
        self.assertTrue(validate_approved_levels([bad], self.words))
        self.assertTrue(validate_approved_levels([self.level], self.words, {"код"}))
        self.assertTrue(validate_approved_levels([dict(self.level, min_moves=3)], self.words))

    def test_versioned_catalog_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "levels.json"
            path.write_text(json.dumps({"version": 1, "levels": [self.level]}), encoding="utf-8")
            self.assertEqual(load_approved_levels(path), [self.level])
            path.write_text(json.dumps({"version": 2, "levels": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_approved_levels(path)

    def test_committed_starter_levels(self):
        levels = load_approved_levels("data/levels_approved.json")
        # The approved catalog grows with every reviewed batch.
        # The small fixture dictionary only covers the original five levels.
        starters = {f"level-{i:03d}" for i in range(1, 6)}
        by_id = {level["id"]: level for level in levels}
        self.assertEqual(len(by_id), len(levels), "Duplicate approved level IDs")
        self.assertTrue(starters.issubset(by_id))
        self.assertEqual(
            validate_approved_levels([by_id[identifier] for identifier in sorted(starters)], self.words),
            [],
        )
        self.assertTrue(all(
            isinstance(level.get("solution"), list) and
            level["solution"][0] == level.get("start") and
            level["solution"][-1] == level.get("end")
            for level in levels
        ))


if __name__ == "__main__":
    unittest.main()
