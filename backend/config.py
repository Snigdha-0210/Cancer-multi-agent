import os

from dotenv import load_dotenv


# Load variables from .env
load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. "
        "Create a .env file in the project root and add your API key."
    )
    