def doc_to_text_arc(doc):
    """Format document as multiple choice prompt for generation."""
    question = doc["question"]
    choices = doc["choices"]["text"]
    labels = doc["choices"]["label"]

    choices_text = "\n".join(
        [f"{label}. {choice}" for label, choice in zip(labels, choices)]
    )

    prompt = (
        f"Питання: {question}\n\n"
        f"{choices_text}\n\n"
        f"Відповідь:"
    )
    return prompt


def doc_to_target_arc(doc):
    """Return the correct answer letter."""
    return doc["answerKey"]
