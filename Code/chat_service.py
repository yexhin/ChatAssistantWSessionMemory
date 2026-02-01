import os
from dotenv import load_dotenv
from google.genai import types
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner

from agents.ChatAssistant import root_agent
from helpers.memory_store import MemoryStore
from helpers.augmentation import build_augmented_user_message
from helpers.context_tracker import (
    count_context_chars,
    should_trigger_summarization,
)
from helpers.session_summarizer import summarize_session
from query_pipelines.query_understanding import QueryUnderstanding

load_dotenv()


class ChatService:
    def __init__(
        self,
        user_id: str,
        session_id: str,
        model: str = "gemini-2.5-flash",
        db_url: str = "sqlite:///./chat_history_data.db",
        app_name: str = "innhi-chat-assistant",
    ):
        self.user_id = user_id
        self.session_id = session_id
        self.model = model
        self.app_name = app_name

        self.session_service = DatabaseSessionService(db_url=db_url)

        self._ensure_session()

        self.runner = Runner(
            agent=root_agent,
            app_name=self.app_name,
            session_service=self.session_service,
        )

        self.memory_store = MemoryStore()
        self.query_understanding = QueryUnderstanding(model=model)

        self.conversation_messages = []
        self.session_summary = self.memory_store.load_summary(session_id)

        self.state = {
            "awaiting_clarification": False,
            "pending_query": None,
            "clarification_attempts": 0,
        }

    def _ensure_session(self):
        """CRITICAL: ADK session must exist in current service"""
        try:
            self.session_service.get_session(
                user_id=self.user_id,
                session_id=self.session_id,
                app_name=self.app_name,
            )
        except Exception:
            self.session_service.create_session(
                user_id=self.user_id,
                session_id=self.session_id,
                app_name=self.app_name,
            )

    async def chat(self, user_input: str) -> dict:
        # 🔥 ENSURE SESSION EVERY TURN
        self._ensure_session()

        # --- normal flow ---
        if self.state["awaiting_clarification"]:
            user_input = (
                self.state["pending_query"]
                + " | User clarification: "
                + user_input
            )
            self.state["awaiting_clarification"] = False
            self.state["pending_query"] = None

        self.conversation_messages.append(
            {"role": "user", "content": user_input}
        )

        raw_messages = self.conversation_messages.copy()

        if should_trigger_summarization(count_context_chars(raw_messages)):
            summary = summarize_session(raw_messages, self.model)
            self.memory_store.save_summary(self.session_id, summary)
            self.session_summary = summary

        qu = self.query_understanding.analyze_query(
            user_query=user_input,
            recent_messages=raw_messages[-3:],
            session_summary=self.session_summary,
        )

        if qu["clarification"]["need_clarification"]:
            self.state["awaiting_clarification"] = True
            self.state["pending_query"] = user_input
            return {
                "type": "clarification",
                "content": qu["clarification"]["questions"],
            }

        final_query = qu["rewrite"].get("rewritten_query", user_input)

        augmented = build_augmented_user_message(
            user_query=final_query,
            session_summary=self.session_summary,
        )

        content = types.Content(
            role="user",
            parts=[types.Part(text=augmented)],
        )

        async for event in self.runner.run_async(
            user_id=self.user_id,
            session_id=self.session_id,
            new_message=content,
        ):
            if event.is_final_response():
                reply = event.content.parts[0].text
                self.conversation_messages.append(
                    {"role": "assistant", "content": reply}
                )
                return {"type": "response", "content": reply}

