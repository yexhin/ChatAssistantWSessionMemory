from google import genai
import os

client = genai.Client(api_key="AIzaSyCyrBFX6KB1paVUbsxhaYDG7gKfeI4d51I")

def call_llm(prompt: str, model="gemini-2.0-flash") -> str:
    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    return response.text