import pymorphy3

morph = pymorphy3.MorphAnalyzer()

for word in ["кот", "собака", "стол", "книга", "бежать"]:
    parse = morph.parse(word)[0]

    print(
        word,
        "->",
        parse.normal_form,
        "|",
        parse.tag
    )