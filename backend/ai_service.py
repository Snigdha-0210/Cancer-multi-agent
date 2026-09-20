from openai import OpenAI

from backend.config import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)


def ask_ai(question: str) -> str:
    response = client.responses.create(
        model="gpt-5.6-luna",
        input=question,
    )

    return response.output_text