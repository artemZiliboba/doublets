
import json
from collections import Counter
from pathlib import Path

import pymorphy3


MIN_LENGTH = 3
MAX_LENGTH = 6
ALPHABET = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")

OUTPUT = Path(__file__).resolve().parent / "data" / "export" / "words.json"


def valid_spelling(word: str) -> bool:
    return (
        MIN_LENGTH <= len(word) <= MAX_LENGTH
        and all(char in ALPHABET for char in word)
    )


def valid_parse(parse, word: str) -> bool:
    tag = parse.tag

    return (
        parse.is_known
        and "NOUN" in tag
        and "nomn" in tag
        and "sing" in tag
        and "Name" not in tag
        and "Surn" not in tag
        and "Patr" not in tag
        and "Geox" not in tag
        and "Orgn" not in tag
        and parse.normal_form == word
    )


def build_dictionary():
    morph = pymorphy3.MorphAnalyzer()
    words = set()

    print("Читаем словарь pymorphy3...")

    for item in morph.dictionary.iter_known_words():
        # В разных версиях итератор может возвращать
        # кортежи с дополнительной информацией.
        word = item[0] if isinstance(item, tuple) else item

        word = word.lower()

        if not valid_spelling(word):
            continue

        # Проверяем все возможные разборы.
        if any(valid_parse(p, word) for p in morph.parse(word)):
            words.add(word)

    result = sorted(words)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nГотово! Сохранено {len(result)} слов.")
    print(f"Файл: {OUTPUT}")

    counts = Counter(map(len, result))
    print("\nРаспределение по длине:")

    for length in range(MIN_LENGTH, MAX_LENGTH + 1):
        print(f"  {length} буквы: {counts[length]}")

    print("\nПервые 30 слов:")
    print(", ".join(result[:30]))


if __name__ == "__main__":
    build_dictionary()
