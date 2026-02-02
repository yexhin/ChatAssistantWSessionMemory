## Introduction
![Innhi's Chat Assistant](images/cover.png)

Hello !! This is my **ChatAssistant** with **Session Memory**, built on top of an **AI Agent architecture using Google Development Kit (GDK)** and LLMs (Gemini).

The goal of this chatbot is simple: behave like a **personal daily assistant** that can remember context, understand vague questions, and respond concisely.

This project is mainly a **backend demo** focusing on:

- Session memory via automatic summarization
- Query understanding & augmentation
- Clean, modular pipeline design

---

## Core Components

### 1. Main Agent (Root Agent)

- The **Root Agent** acts as:
    - Orchestrator
    - Final response generator
- Implemented using **Google ADK**

Agent configuration:

```python
model = "gemini-2.5-flash"
description = "A AI chat assistant that answers user questions based on provided context and history."
instruction = """
You are a helpful AI assistant. Your task is:
- Answer user questions accurately and concisely. LESS THAN 200 WORDS
- Provide explanations ONLY when necessary.
- Do NOT assume access to full conversation history unless it is explicitly included.

RULES:
- Maximum length: 3–5 sentences total.
- NO long explanations.
- NO examples unless explicitly asked.
- NO introductions, summaries, or filler phrases.
- Do NOT repeat the question back to the user.

FORMAT RULE:
- Prefer bullet points when possible.
- Keep language direct and neutral.
"""

```

---

### 2. Context Tracker

- Helper functions to:
    - Count total characters in the conversation
    - Decide when session summarization should be triggered
- Uses a **simple heuristic (character-based)** threshold

```python
def count_context_chars(messages: List[Dict[str, str]]) -> int:
    """
    Count total number of characters in conversation messages.
    Each message is expected to have a 'content' field.
    """
    return sum(len(msg.get("content", "")) for msg in messages)

def should_trigger_summarization(context_size: int) -> bool:
    """
    Decide whether session summarization should be triggered.
    """
    threshold = 10000
    return context_size >= threshold

```

---

### 3. LLM Invocation for Summarization & Query Understanding
- The system uses Large Language Models (LLMs) as reasoning components for both session summarization and query understanding.
- LLM calls are abstracted behind a lightweight helper function to ensure:
    - Reusability across different pipeline stages
    - Centralized model configuration
    - Easy replacement of LLM providers (e.g. Gemini, OpenAI, Claude)

Currently, the project uses Gemini models via the Google GenAI SDK.
- A helper function supports the Summarizer & Query Understanding calling LLMs to implement the summarization & analyzing queries.
  
  ```python
  from google import genai
  import os
  client = genai.Client(api_key="AIzaSyCyrBFX6KB1paVUbsxhaYDG7gKfeI4d51I")

  def call_llm(prompt: str, model="gemini-2.0-flash") -> str:
    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    return response.text
  ```

### 4. Session Summarizer

- Responsible for converting **raw conversation history** into **structured session memory**
- Follows a **strict JSON schema** defined in `schemas/`
- Uses **Gemini (via Google API key)** to parse and summarize the conversation

Prompt structure:

```python
conversation_text = "\n".join(
    f"{m['role']}: {m['content']}" for m in messages
)

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

raw_output = call_llm(prompt=instruction, model="gemini-2.5-pro")

```

---

### 5. Query Understanding Pipeline
This pipeline is split into **two clear stages** for easier management:

- `query_understanding.py`
    - Analyze the raw user query
    - Detect ambiguity
    - Rewrite or clarify intent
- `augmentation.py`
    - Build the **augmented prompt** for the Root Agent
    - Combine:
        - Recent messages
        - Relevant session memory fields

---

## How to Set Up

1. Install required libraries
```bash
pip install -r requirements.txt
```

2. Run the application:

```bash
python -m main
```

3. Start chatting 🎉

---

## Pipeline
![Chat Assistant Pipeline](images/ChatAssist_UserFlow.png)

## Code Structure

```
project_root/
│
├── main.py
│
├── agents/
│   └── root_agent.py
│
├── helpers/
│   ├── context_tracker.py
│   ├── memory_store.py
│   ├── session_summarizer.py
│   ├── augmentation.py
│   └── call_llms.py
│
├── query_pipeline/
│   └── query_understanding.py
│
└── schemas/
    └── schema_summary.py

```

---

## Assumptions & Limitations

- Token counting is **character-based**, not tokenizer-based
- Session memory is **short-term only** (stored locally)
- Designed as a **demo backend**, not a production-ready system

---

# Demo output
### Flow 1: 
```bash
Chat started. Type 'exit' to quit.
How can I help you today?


=== USER MESSAGE ===
You: Give me a full overview of how session memory works in this assistant.

===================
[Context] Current size: 142 chars

=== QUERY UNDERSTANDING (JSON) ===
{
  "original_query": "Give me a full overview of how session memory works in this assistant.",
  "is_ambiguous": false,
  "rewritten_query": null,
  "need_clarification": false,
  "clarifying_questions": [],
  "used_session_summary": false
}
=================================

=== ASSISTANT RESPONSE ===
Assistant:
- Session memory stores recent conversation turns.
- When the context exceeds a predefined threshold, summarization is triggered.
- The summary replaces older messages and is reused in future queries.

==========================


=== USER MESSAGE ===
You: Can you explain how summarization is triggered and stored?

===================
[Context] Current size: 386 chars


=== USER MESSAGE ===
You: What kind of data does the summary usually contain?

===================
[Context] Current size: 612 chars

[Memory] Context limit exceeded at 612 chars
[Memory] Triggering session summarization...

Generated Session Summary:
{
  "session_summary": {
    "user_profile": {
      "prefs": [],
      "constraints": []
    },
    "key_facts": [
      "User is exploring session memory and summarization behavior"
    ],
    "decisions": [
      "Summarization is used when context exceeds a threshold"
    ],
    "open_questions": [
      "How to optimize summarization granularity?"
    ],
    "todos": []
  },
  "message_range_summarized": {
    "from": 0,
    "to": 5
  }
}

```

### Flow 2:
``` bash
=== USER MESSAGE ===
You: How do I make matcha?

===================
[Context] Current size: 128 chars

=== QUERY UNDERSTANDING (JSON) ===
{
  "original_query": "How do I make matcha?",
  "is_ambiguous": true,
  "rewritten_query": "How do I make a basic cup of matcha tea at home?",
  "need_clarification": true,
  "clarifying_questions": [
    "Do you want traditional hot matcha or a matcha latte?",
    "Do you have a bamboo whisk available?"
  ],
  "used_session_summary": true
}
=================================

Assistant (clarifying):
--------
 Do you want traditional hot matcha or a matcha latte?
--------
--------
 Do you have a bamboo whisk available?
--------
```

---
## Notes

This project was built for Vulcan Lab:

- Clean agent pipeline design
- Schema-first LLM outputs
- Practical session memory handling

