def doc_to_text(doc):
    """Format document as multiple choice prompt for generation."""
    passage = doc["flores_passage"]
    question = doc["question"]
    answers = [
        doc["mc_answer1"],
        doc["mc_answer2"],
        doc["mc_answer3"],
        doc["mc_answer4"],
    ]

    choices_text = "\n".join(
        [f"{i+1}. {answer}" for i, answer in enumerate(answers)]
    )

    prompt = (
        f"Уривок: {passage}\n\n"
        f"Питання: {question}\n\n"
        f"{choices_text}\n\n"
        f"Відповідь (введіть номер 1, 2, 3 або 4):"
    )
    return prompt


def doc_to_target(doc):
    """Return the correct answer number as string."""
    return str(doc["correct_answer_num"])
