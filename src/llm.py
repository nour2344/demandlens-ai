
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


load_dotenv()


def get_llm():
    """Initialize the shared language model."""

    if not os.getenv("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY is missing.")

    return ChatGroq(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        temperature=0,
        max_tokens=1024,
        timeout=60,
        max_retries=2
    )
