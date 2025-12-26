"""
Common filter functions for Ukrainian LLM benchmark tasks.
Used to handle thinking models that output <think>...</think> tags.
"""

import re
from typing import List


def strip_thinking_tags(resps: List[str], docs=None) -> List[str]:
    """
    Filter function to strip <think>...</think> tags from model responses.
    Works with Qwen3, DeepSeek-R1, and other thinking models.

    Args:
        resps: List of model response strings
        docs: Optional document context (not used, but required by lm-eval filter interface)

    Returns:
        List of responses with thinking tags removed
    """
    cleaned = []
    for resp in resps:
        # Remove <think>...</think> blocks (including empty ones)
        clean = re.sub(r'<think>.*?</think>\s*', '', resp, flags=re.DOTALL)
        # Also handle </think> without opening tag (partial responses)
        clean = re.sub(r'.*?</think>\s*', '', clean, flags=re.DOTALL)
        cleaned.append(clean.strip())
    return cleaned


def extract_answer_letter(resps: List[str], docs=None) -> List[str]:
    """
    Extract single letter answer (A-D or 1-4) from response.
    Strips thinking tags first, then extracts the answer.

    Args:
        resps: List of model response strings
        docs: Optional document context

    Returns:
        List of extracted answer letters (uppercase)
    """
    results = []
    for resp in resps:
        # First strip thinking tags
        clean = re.sub(r'<think>.*?</think>\s*', '', resp, flags=re.DOTALL)
        clean = re.sub(r'.*?</think>\s*', '', clean, flags=re.DOTALL)

        # Try to find answer letter
        # Look for patterns like "B", "B.", "B)", "Answer: B", "Відповідь: B"
        match = re.search(r'\b([A-Da-d])\b', clean)
        if match:
            results.append(match.group(1).upper())
        else:
            # Try numeric answers (1-4)
            match = re.search(r'\b([1-4])\b', clean)
            if match:
                # Convert 1-4 to A-D
                num_to_letter = {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}
                results.append(num_to_letter.get(match.group(1), match.group(1)))
            else:
                # No answer found, return empty
                results.append('')
    return results
