from typing import List, Dict

def count_context_chars(
    messages: List[Dict[str, str]]) -> int:
    """
    Count total number of characters in conversation messages.
    Each message is expected to have a 'content' field.
    """
    return sum(len(msg.get("content", "")) for msg in messages)


def should_trigger_summarization(context_size: int ) -> bool:
    """
    Decide whether session summarization should be triggered.
    """
    
    threshold = 2000 # Define threshold for summarization
    return context_size >= threshold
