import unittest

from doublets.engine import WordGraph
from doublets.levels import generate_levels


class DualDictionaryLevelTests(unittest.TestCase):
    def setUp(self):
        self.extended = ["кот", "кит", "бит", "бот", "быт", "дом"]
        self.core = ["кот", "бит", "дом"]

    def test_endpoints_and_shortest_solution(self):
        levels = generate_levels(self.core, self.extended, count=10, min_moves=2,
                                 max_moves=3, seed=3)
        self.assertTrue(levels)
        graph = WordGraph(self.extended)
        for level in levels:
            self.assertIn(level["start"], self.core)
            self.assertIn(level["end"], self.core)
            self.assertEqual(len(level["solution"]) - 1, level["min_moves"])
            self.assertEqual(len(graph.shortest_path(level["start"], level["end"])) - 1,
                             level["min_moves"])
            self.assertTrue(all(graph.validate_move(a, b)
                                for a, b in zip(level["solution"], level["solution"][1:])))
        self.assertEqual(len(levels), len({tuple(sorted((l["start"], l["end"])))
                                           for l in levels}))

    def test_seed_reproducible_independent_of_input_order(self):
        first = generate_levels(self.core, self.extended, seed=10)
        second = generate_levels(list(reversed(self.core)),
                                 list(reversed(self.extended)), seed=10)
        self.assertEqual(first, second)

    def test_core_not_in_extended(self):
        with self.assertRaises(ValueError):
            generate_levels(["ёжик"], self.extended)

    def test_empty_and_invalid_parameters(self):
        self.assertEqual(generate_levels([], [], count=5), [])
        self.assertEqual(generate_levels(self.core, self.extended, count=0), [])
        for kwargs in ({"count": -1}, {"min_moves": 0},
                       {"min_moves": 4, "max_moves": 2}):
            with self.assertRaises(ValueError):
                generate_levels(self.core, self.extended, **kwargs)

    def test_only_extended_intermediate(self):
        levels = generate_levels(["кот", "бит"], ["кот", "кит", "бит"],
                                 min_moves=2, max_moves=2, seed=1)
        self.assertEqual(len(levels), 1)
        self.assertEqual(levels[0]["solution"], ["бит", "кит", "кот"])


if __name__ == "__main__":
    unittest.main()
