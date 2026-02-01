import sys
import os

# Add parent directory to path FIRST (before any local imports)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

import streamlit as st
import asyncio
from chat_service import ChatService

st.set_page_config(page_title="Innhi Chat Assistant", layout="centered")
st.title("Chat Assistant")

SESSION_ID = "streamlit_session"
USER_ID = "streamlit_user"

if "chat_service" not in st.session_state:
    st.session_state.chat_service = ChatService(
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("assistant"):
        result = asyncio.run(
            st.session_state.chat_service.chat(user_input)
        )

        if result["type"] == "clarification":
            text = "\n".join(f"- {q}" for q in result["content"])
        else:
            text = result["content"]

        st.markdown(text)
        st.session_state.messages.append(
            {"role": "assistant", "content": text}
        )
