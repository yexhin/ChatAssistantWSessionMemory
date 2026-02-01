from typing import List, Dict
import json

from helpers.call_llms import call_llm
from schemas.session_summary import SessionSummary


def extract_json(text: str) -> str:
    text = text.strip()

    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()

    return text


def summarize_session(
        messages: List[Dict[str, str]],
        model: str,) -> SessionSummary:
    """
    Summarize a chat session into structured short-term memory.
    """

    conversation_text = "\n".join(f"{m['role']}: {m['content']}" for m in messages)

    instruction = f"""
        You are a system component that summarizes chat sessions into memory.

        Your output MUST be a valid JSON object.
        Do NOT include markdown, comments, or extra text.

        The JSON MUST strictly follow this schema:

        {{
        "session_intent": string | null,
        "user_profile": object,
        "key_facts": string[],
        "decisions": string[],
        "constraints": string[],
        "open_questions": string[],
        "todos": string[],
        "summary_text": string | null
        }}

        Rules:
        - All fields MUST be present.
        - Use null instead of missing values.
        - Use empty arrays or empty objects if no data.
        - Output JSON ONLY.

        Conversation:
        {conversation_text}
        """

                
    raw_output = call_llm(prompt=instruction, model=model)

    if not raw_output or not raw_output.strip():
        raise ValueError("LLM returned empty output for session summary")

    print("[DEBUG] Raw summary output:")
    print(raw_output)

    try:
        clean_output = extract_json(raw_output)
        data = json.loads(clean_output)
        return SessionSummary(**data)

    except Exception as e:
        raise ValueError(
            f"Failed to parse session summary.\nRaw output:\n{raw_output}\nError: {e}"
        )
