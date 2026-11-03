import pymorphy3

morph = pymorphy3.MorphAnalyzer()

print("Путь к словарю:")
print(morph.dictionary.path)

print("\nТип объекта dictionary:")
print(type(morph.dictionary))

print("\nДоступные атрибуты:")
for name in dir(morph.dictionary):
    if not name.startswith("_"):
        print(name)

print("\nТип объекта words:")
if hasattr(morph.dictionary, "words"):
    print(type(morph.dictionary.words))
else:
    print("Атрибут words отсутствует")