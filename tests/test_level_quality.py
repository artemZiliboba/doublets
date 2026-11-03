import unittest

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

    def test_default_length_restricts_six_letter_levels(self):
        self.assertEqual(generate_levels(["машина"], ["машина"]), [])
        with self.assertRaises(ValueError):
            generate_levels([], [], min_length=5, max_length=4)


if __name__ == "__main__":
    unittest.main()
