import asyncio
import json
import os
from dotenv import load_dotenv
from google.genai import types

from agents.ChatAssistant import root_agent
from helpers.memory_store import MemoryStore
from helpers.augmentation import build_augmented_user_message
from helpers.context_tracker import count_context_chars, should_trigger_summarization
from helpers.session_summarizer import summarize_session
from query_pipelines.query_understanding import QueryUnderstanding

from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner

# ENV & CONFIG
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

MODEL = "gemini-2.5-flash"
DB_URL = "sqlite:///./chat_history_data.db"


async def main():
    user_id = "demo_user"
    session_id = "demo_session"

    # Services
    session_service = DatabaseSessionService(db_url=DB_URL)
    memory_store = MemoryStore()
    query_understanding = QueryUnderstanding(model=MODEL)

    runner = Runner(
        agent=root_agent,
        app_name="innhi-chat-assistant",
        session_service=session_service,
    )
    
    try:
        await session_service.create_session(
            user_id=user_id,
            session_id=session_id,
            app_name="innhi-chat-assistant",
        )
    except Exception:
        pass

    
    MAX_SHORT_MEMORY_TURNS = 12

  
    #MEMORY & STATE
    conversation_messages = []  # short-term memory

    session_summary = memory_store.load_summary(session_id)

    session_state = {
        "session_summary": session_summary,
        "last_query_understanding": None,
        "awaiting_clarification": False,
        "pending_query": None,
        "clarification_attempts": 0,  
    }

    print("Chat started. Type 'exit' to quit.")
    print("How can I help you today?\n")

  
    # CHAT LOOP
    while True:
        try:
            print("\n=== USER MESSAGE ===")
            user_input = input("You: ").strip()
            print("\n===================")
        except EOFError:
            print("\n[System] Input closed. Bye.")
            break

        if user_input.lower() in ["exit", "quit"]:
            break

        if session_state["awaiting_clarification"]:
            user_input = (
                session_state["pending_query"]
                + " | User clarification: "
                + user_input
            )
            session_state["awaiting_clarification"] = False
            session_state["pending_query"] = None
            session_state["clarification_attempts"] = 0

        conversation_messages.append({"role": "user", "content": user_input})

        raw_messages = conversation_messages.copy()
        context_size = count_context_chars(raw_messages)

        if should_trigger_summarization(context_size):
            print(f"[Memory] Summarizing at {context_size} chars")
            session_summary = summarize_session(raw_messages, MODEL)
            memory_store.save_summary(session_id, session_summary)
            session_state["session_summary"] = session_summary
            conversation_messages = conversation_messages[-4:]

        qu_result = query_understanding.analyze_query(
            user_query=user_input,
            recent_messages=raw_messages[-3:],
            session_summary=session_summary,
        )

        rewrite = qu_result.get("rewrite", {})
        clarification = qu_result.get("clarification", {})

        is_ambiguous = rewrite.get("is_ambiguous", False)
        need_clarification = clarification.get("need_clarification", False)

        if is_ambiguous and session_state["clarification_attempts"] >= 1:
            need_clarification = False

        
        debug_output = {
            "original_query": user_input,
            "is_ambiguous": rewrite.get("is_ambiguous", False),
            "rewritten_query": rewrite.get("rewritten_query"),
            "need_clarification": clarification.get("need_clarification", False),
            "clarifying_questions": clarification.get("questions", []),
            "used_session_summary": bool(session_summary),
        }

        print("\n=== QUERY UNDERSTANDING (JSON) ===")
        print(json.dumps(debug_output, indent=2))
        print("=================================\n")

        final_user_query = (
            rewrite.get("rewritten_query", user_input)
            if is_ambiguous else user_input
        )

        if need_clarification:
            session_state["awaiting_clarification"] = True
            session_state["pending_query"] = final_user_query
            session_state["clarification_attempts"] += 1

            print("Assistant (clarifying):")
            for q in clarification.get("questions", []):
                print("--------\n", q)
                print("--------")
            continue

        augmented_query = build_augmented_user_message(
            user_query=final_user_query,
            session_summary=session_summary,
        )

        content = types.Content(
            role="user",
            parts=[types.Part(text=augmented_query)],
        )

       
        # RUN ROOT AGENT
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if event.is_final_response():
                reply = event.content.parts[0].text
                print("\n=== ASSISTANT RESPONSE ===")
                print("Assistant:", reply)
                print("\n==========================")

                conversation_messages.append({
                    "role": "assistant",
                    "content": reply,
                })

                if len(conversation_messages) > MAX_SHORT_MEMORY_TURNS:
                    conversation_messages = conversation_messages[-MAX_SHORT_MEMORY_TURNS:]

    print("See you later, buddy!")


if __name__ == "__main__":
    asyncio.run(main())
