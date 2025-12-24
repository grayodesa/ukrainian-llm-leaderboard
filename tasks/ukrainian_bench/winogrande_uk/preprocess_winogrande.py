def doc_to_text(doc):
    answer_to_num = {"1": 0, "2": 1}
    return answer_to_num[doc["answer"]]


def doc_to_target(doc):
    idx = doc["sentence"].index("_") + 1
    return doc["sentence"][idx:].strip()


def doc_to_choice(doc):
    idx = doc["sentence"].index("_")
    options = [doc["option1"], doc["option2"]]
    return [doc["sentence"][:idx] + opt for opt in options]


def doc_to_text_generate(doc):
    """Format document as multiple choice prompt for generation."""
    sentence = doc["sentence"]
    option1 = doc["option1"]
    option2 = doc["option2"]

    prompt = (
        f"Заповніть пропуск (_) у реченні правильним варіантом:\n\n"
        f"Речення: {sentence}\n\n"
        f"A. {option1}\n"
        f"B. {option2}\n\n"
        f"Відповідь:"
    )
    return prompt


def doc_to_target_generate(doc):
    """Return the correct answer letter (A or B)."""
    answer_to_letter = {"1": "A", "2": "B"}
    return answer_to_letter[doc["answer"]]
