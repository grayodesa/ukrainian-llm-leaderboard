import re

import datasets


def preprocess(text):
    text = text.strip()
    # NOTE: Brackets are artifacts of the WikiHow dataset portion of HellaSwag.
    text = text.replace(" [title]", ". ")
    text = re.sub("\\[.*?\\]", "", text)
    text = text.replace("  ", " ")
    return text


def process_docs(dataset: datasets.Dataset) -> datasets.Dataset:
    def _process_doc(doc):
        ctx = doc["ctx_a"] + " " + doc["ctx_b"].capitalize()
        out_doc = {
            "query": preprocess(doc["activity_label"] + ": " + ctx),
            "choices": [preprocess(ending) for ending in doc["endings"]],
            "gold": int(doc["label"]),
            "label": int(doc["label"]),
        }
        return out_doc

    return dataset.map(_process_doc)


def doc_to_text_generate(doc):
    """Format document as multiple choice prompt for generation."""
    options = ["A", "B", "C", "D"]
    choices_text = "\n".join(
        [f"{opt}. {choice}" for opt, choice in zip(options, doc["choices"])]
    )
    prompt = (
        f"{doc['query']}\n\n"
        f"Оберіть найкращий варіант продовження:\n"
        f"{choices_text}\n\n"
        f"Відповідь:"
    )
    return prompt


def doc_to_target_generate(doc):
    """Return the correct answer letter."""
    options = ["A", "B", "C", "D"]
    return options[doc["gold"]]