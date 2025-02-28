import os
from langchain_google_genai import ChatGoogleGenerativeAI

def get_gemini(model):
    llm = ChatGoogleGenerativeAI(model=model, google_api_key = os.getenv("GEMINI_API_KEY_BETA"))
    return llm

gemini_flash = get_gemini("gemini-2.0-flash")