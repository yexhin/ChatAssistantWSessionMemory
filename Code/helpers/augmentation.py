from typing import List, Dict, Optional
from schemas.session_summary import SessionSummary


def build_augmented_user_message(
    user_query: str,
    recent_messages: Optional[List[Dict[str, str]]] = None,
    session_summary: Optional[SessionSummary] = None,
    max_recent_messages: int = 3, ) -> str:
    """
    Build an augmented prompt for the root agent by combining:
    - Recent conversation messages
    - Relevant fields from session summary
    """

    sections = []

    # Recent conversation 
    if recent_messages:
        recent_block = []
        for msg in recent_messages[-max_recent_messages:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            recent_block.append(f"{role}: {content}")

        sections.append(
            "Recent conversation:\n" + "\n".join(recent_block)
        )

    # Session summary
    if session_summary:
        summary_parts = []

        if session_summary.session_intent:
            summary_parts.append(f"Session intent:\n{session_summary.session_intent}")

        if session_summary.key_facts:
            summary_parts.append(
                "Key facts:\n- " + "\n- ".join(session_summary.key_facts)
            )

        if session_summary.decisions:
            summary_parts.append(
                "Decisions made so far:\n- " + "\n- ".join(session_summary.decisions)
            )

        if session_summary.constraints:
            summary_parts.append(
                "Constraints:\n- " + "\n- ".join(session_summary.constraints)
            )

        if session_summary.open_questions:
            summary_parts.append(
                "Open questions:\n- " + "\n- ".join(session_summary.open_questions)
            )

        if summary_parts:
            sections.append(
                "Session memory:\n" + "\n\n".join(summary_parts)
            )

    # Final augmented prompt
    if sections:
        return (
            "\n\n".join(sections)
            + "\n\n"
            + f"Current user question:\n{user_query}\n\n"
            + "Please answer consistently with the context above."
        )

    return user_query
