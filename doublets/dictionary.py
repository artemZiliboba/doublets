"""Import OpenCorpora XML dictionary; no network access required."""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

WORD = re.compile(r'^[а-яё]{3,6}$')
EXCLUDE = {'Name', 'Surn', 'Patr', 'Geox', 'Orgn', 'Abbr', 'Init', 'Fixd'}


def extract_nouns(xml_path):
    """Select singular nominative NOUN forms from lexemes tagged NOUN.

    Some plural-only nouns have no singular nominative form and are excluded.
    Proper nouns and abbreviations are excluded using OpenCorpora grammemes.
    """
    output = set()
    for _, element in ET.iterparse(xml_path, events=('end',)):
        if element.tag != 'lemma':
            continue
        base = element.find('l')
        if base is None:
            element.clear()
            continue
        base_tags = {g.get('v') for g in base.findall('g')}
        if 'NOUN' not in base_tags or base_tags & EXCLUDE:
            element.clear()
            continue
        for form in element.findall('f'):
            tags = base_tags | {g.get('v') for g in form.findall('g')}
            word = (form.get('t') or '').lower()
            if {'nomn', 'sing'} <= tags and not tags & EXCLUDE and WORD.fullmatch(word):
                output.add(word)
        element.clear()
    return sorted(output)


def export_words(words, output):
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps({'version': 1, 'rules': {'pos': 'NOUN', 'case': 'nomn', 'number': 'sing', 'min_length': 3, 'max_length': 6, 'yo_separate': True}, 'words': sorted(set(words))}, ensure_ascii=False, indent=2), encoding='utf-8')
