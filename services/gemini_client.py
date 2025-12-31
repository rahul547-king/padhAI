import os
from google import genai


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not found. Check your .env file."
        )

    return genai.Client(api_key=api_key)


def generate_answer(prompt: str) -> str:
    client = get_gemini_client()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text
