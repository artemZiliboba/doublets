"""Export 3-6 character Russian noun lemmas from installed pymorphy3.

Requires: pip install -r requirements.txt
"""
import argparse
import json
from collections import Counter
from pathlib import Path

MIN_LENGTH = 3
MAX_LENGTH = 6
ALPHABET = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
EXCLUDE = {"Name", "Surn", "Patr", "Geox", "Orgn", "Abbr", "Init"}
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "data" / "export" / "words.json"


def valid_spelling(word):
    return MIN_LENGTH <= len(word) <= MAX_LENGTH and all(char in ALPHABET for char in word)


def valid_parse(parse, word):
    tag = parse.tag
    return (
        parse.is_known
        and "NOUN" in tag
        and "nomn" in tag
        and "sing" in tag
        and not any(g in tag for g in EXCLUDE)
        and parse.normal_form == word
    )


def extract_pymorphy_nouns(morph):
    words = set()
    for item in morph.dictionary.iter_known_words():
        word = item[0] if isinstance(item, tuple) else item
        word = word.lower()
        if valid_spelling(word) and any(valid_parse(p, word) for p in morph.parse(word)):
            words.add(word)
    return sorted(words)


def build_dictionary(output=DEFAULT_OUTPUT):
    import pymorphy3

    print("Читаем словарь pymorphy3...")
    result = extract_pymorphy_nouns(pymorphy3.MorphAnalyzer())
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Same schema as the legacy XML exporter. Readers also accept older JSON arrays.
    from doublets.dictionary import export_words
    export_words(result, output)
    print(f"Сохранено {len(result)} слов: {output}")
    for length, count in sorted(Counter(map(len, result)).items()):
        print(f"  {length} букв: {count}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    build_dictionary(args.out)
