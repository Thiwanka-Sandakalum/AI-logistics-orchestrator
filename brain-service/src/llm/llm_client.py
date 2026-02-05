"""
Gemini LLM client for intent detection using LangChain's ChatGoogleGenerativeAI.
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI

# Load .env if present
from dotenv import load_dotenv
load_dotenv()

# You must set GOOGLE_API_KEY in your environment
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

def get_gemini_llm():
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API key required for Gemini Developer API. Set GOOGLE_API_KEY or GEMINI_API_KEY.")
    return ChatGoogleGenerativeAI(model=MODEL_NAME, api_key=api_key)

async def detect_intent_with_gemini(message: str) -> str:
    llm = get_gemini_llm()
    prompt = (
        "You are an intent classifier for a shipping assistant. "
        "Classify the user's request as one of: 'pricing', 'tracking', or 'label'. "
        "Respond ONLY with the intent word.\n"
        f"User: {message}"
    )
    # Gemini API is sync, so run in thread for async
    from concurrent.futures import ThreadPoolExecutor
    import asyncio
    loop = asyncio.get_event_loop()
    def sync_invoke():
        return llm.invoke(prompt).content if hasattr(llm.invoke(prompt), 'content') else llm.invoke(prompt)
    result = await loop.run_in_executor(ThreadPoolExecutor(), sync_invoke)
    return result.strip().lower()
