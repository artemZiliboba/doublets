import unittest
from pathlib import Path

from doublets.dictionary_quality import read_exclusions, prepare_quality

from doublets.engine import WordGraph
from doublets.levels import generate_levels, preferred_shortest_path, summarize_levels


class LevelQualityTests(unittest.TestCase):
    def test_exclusions_rebuild_graph_and_remove_endpoints(self):
        extended = ["кот", "кит", "бит"]
        self.assertEqual(generate_levels(["кот", "бит"], extended,
                         min_moves=2, max_moves=2, max_length=3,
                         exclusions={"кит"}), [])
        self.assertEqual(generate_levels(["кот", "бит"], extended,
                         exclusions={"кот"}), [])

    def test_prefer_familiar_shortest_route(self):
        graph = WordGraph(["кот", "кит", "бит", "бот"])
        self.assertEqual(preferred_shortest_path(graph, "кот", "бит",
                         {"кот", "бит", "бот"}, {}),
                         ["кот", "бот", "бит"])

    def test_frequency_breaks_ties(self):
        graph = WordGraph(["кот", "кит", "бит", "бот"])
        self.assertEqual(preferred_shortest_path(graph, "кот", "бит",
                         graph.words, {"кит": 100, "бот": 1}),
                         ["кот", "кит", "бит"])

    def test_review_report(self):
        levels = generate_levels(["кот", "бит"], ["кот", "кит", "бит"],
                                 count=1, min_moves=2, max_moves=2)
        report = summarize_levels(levels)
        self.assertEqual(report["generated"], 1)
        self.assertEqual(report["unfamiliar_intermediate_words"], {"кит": 1})

    def test_editorial_exclusions_apply_to_both_dictionaries(self):
        excluded = read_exclusions(Path("data/quality/excluded_words.txt"))
        self.assertTrue({"хуй", "сука", "бри", "дук"} <= excluded)
        result = prepare_quality(
            ["хуй", "сука", "бри", "кот", "кит", "бит"],
            exclusions=excluded,
            frequencies={"хуй": 1000, "сука": 1000, "кот": 1000, "кит": 1000, "бит": 1000},
            min_frequency=1,
        )
        self.assertEqual(result["core"], ["бит", "кит", "кот"])
        self.assertEqual(result["extended"], ["бит", "кит", "кот"])
        levels = generate_levels(
            ["хуй", "сука", "кот", "бит"], ["хуй", "сука", "кот", "кит", "бит"],
            exclusions=excluded, min_moves=2, max_moves=2,
        )
        self.assertTrue(all(not (set(level["solution"]) & excluded) for level in levels))

    def test_default_length_restricts_six_letter_levels(self):
        self.assertEqual(generate_levels(["машина"], ["машина"]), [])
        with self.assertRaises(ValueError):
            generate_levels([], [], min_length=5, max_length=4)


if __name__ == "__main__":
    unittest.main()
