import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from doublets import WordGraph, one_letter_apart, extract_nouns

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.g = WordGraph(['кот', 'кит', 'бит', 'бот', 'быт', 'дом', 'дым', 'ёжик', 'ежик'])

    def test_one_letter(self):
        self.assertTrue(one_letter_apart('кот', 'кит'))
        self.assertFalse(one_letter_apart('кот', 'дом'))
        self.assertFalse(one_letter_apart('кот', 'коты'))

    def test_path(self):
        path = self.g.shortest_path('кот', 'бит')
        self.assertEqual(len(path), 3)
        self.assertTrue(all(self.g.validate_move(a, b) for a,b in zip(path, path[1:])))

    def test_unreachable(self):
        self.assertIsNone(self.g.shortest_path('кот', 'дом'))

    def test_yo(self):
        self.assertIn('ёжик', self.g.words)
        self.assertIn('ежик', self.g.words)
        self.assertTrue(self.g.validate_move('ёжик', 'ежик'))

    def test_random_level(self):
        level = self.g.random_level(2, 2, seed=2)
        self.assertEqual(level['min_moves'], 2)
        self.assertEqual(len(self.g.shortest_path(level['start'], level['end'])) - 1, 2)

    def test_xml(self):
        xml = '''<dictionary><lemmata>
        <lemma id="1"><l t="кот"><g v="NOUN"/></l><f t="кот"><g v="sing"/><g v="nomn"/></f><f t="кота"><g v="sing"/><g v="gent"/></f></lemma>
        <lemma id="2"><l t="Москва"><g v="NOUN"/><g v="Geox"/></l><f t="Москва"><g v="sing"/><g v="nomn"/></f></lemma>
        <lemma id="3"><l t="бегать"><g v="INFN"/></l><f t="бегать"/></lemma>
        </lemmata></dictionary>'''
        with TemporaryDirectory() as d:
            f = Path(d) / 'test.xml'; f.write_text(xml, encoding='utf-8')
            self.assertEqual(extract_nouns(f), ['кот'])

if __name__ == '__main__': unittest.main()
