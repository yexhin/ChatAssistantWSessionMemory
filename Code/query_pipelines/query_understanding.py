from typing import Dict, List, Optional
from helpers.call_llms import call_llm
from schemas.session_summary import SessionSummary
import json


class QueryUnderstanding:
    """
    Query Understanding Pipeline:
    - Ambiguity detection
    - Query rewriting
    - Clarifying question generation
    """

    def __init__(self, model: str):
        self.model = model

    def _build_augmented_context(
        self,
        recent_messages: Optional[List[Dict[str, str]]],
        session_summary: Optional[SessionSummary],
    ) -> str:
        parts = []

        if recent_messages:
            parts.append("Recent conversation:")
            for msg in recent_messages:
                parts.append(f"{msg['role']}: {msg['content']}")

        if session_summary:
            if session_summary.session_intent:
                parts.append(f"Session intent: {session_summary.session_intent}")

            if session_summary.key_facts:
                parts.append(
                    "Key facts:\n- " + "\n- ".join(session_summary.key_facts)
                )

            if session_summary.open_questions:
                parts.append(
                    "Open questions:\n- " + "\n- ".join(session_summary.open_questions)
                )

        return "\n".join(parts) if parts else "No prior context available."

    def analyze_query(
        self,
        user_query: str,
        recent_messages: Optional[List[Dict[str, str]]] = None,
        session_summary: Optional[SessionSummary] = None,
    ) -> Dict:
        augmented_context = self._build_augmented_context(
            recent_messages=recent_messages,
            session_summary=session_summary,
        )

        prompt = f"""
            You are a Query Understanding module in a conversational AI system.

            Context:
            {augmented_context}

            User query:
            "{user_query}"

            Tasks:
            1. Decide if the query is ambiguous.
            2. If ambiguous, rewrite it clearly.
            3. Decide if clarifying questions are required.

            Return ONLY valid JSON in this exact structure:

            {{
            "rewrite": {{
                "is_ambiguous": true | false,
                "rewritten_query": ""
            }},
            "clarification": {{
                "need_clarification": true | false,
                "questions": []
            }}
            }}
            """

        raw_text = call_llm(prompt, model=self.model)
        return self._parse_response(raw_text, user_query)

  
    # Robust JSON parsing
    def _parse_response(self, text: str, original_query: str) -> Dict:
        try:
            cleaned = text.strip()

            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]

            data = json.loads(cleaned)

            return {
                "original_query": original_query,
                "rewrite": data.get("rewrite", {
                    "is_ambiguous": False,
                    "rewritten_query": ""
                }),
                "clarification": data.get("clarification", {
                    "need_clarification": False,
                    "questions": []
                }),
            }

        except Exception as e:
            return {
                "original_query": original_query,
                "rewrite": {
                    "is_ambiguous": False,
                    "rewritten_query": "",
                },
                "clarification": {
                    "need_clarification": False,
                    "questions": [],
                },
                "error": f"Failed to parse LLM output: {e}",
            }
