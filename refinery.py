"""
Backend logic of demo, responsible for interfacing with Accenture AI Refinery
API.
"""

import asyncio
import os

from air import AIRefinery, DistillerClient
from dotenv import load_dotenv
from air.types.chat import ChatCompletion

# API key loaded from .env file.
load_dotenv()
API_KEY: str | None = os.getenv("API_KEY")
MISSING_KEY_WARN: str = "API Key not found, be sure to create a .env file holding your API key!"

# air config path.
#CONFIG_PATH: str = f"{APP_NAME}.yaml"

# Client for interfacing w/ Accenture AI Refinery. Similar to OpenAI API v1 client model.
AIR_CLIENT: AIRefinery | None = AIRefinery(api_key=API_KEY) if API_KEY is not None else None

# LLM in use for chat completions.
LANGUAGE_MODEL: str = "meta-llama/Llama-3.3-70b-Instruct"

def generate_response(query: str) -> str | None:
    """
    Get a response from model `LANGUAGE_MODEL` to the given user-query as
    a string.
    """
    if AIR_CLIENT is None:
        print(MISSING_KEY_WARN)
        return None
    
    prompt: str = f"Respond to the following user query: \n\n{query}"
    response: ChatCompletion = AIR_CLIENT.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt}
        ],
        model=LANGUAGE_MODEL
    )
    return response.choices[0].message.content

