"""Async Google Gemini LLM wrapper for Streaming and State Extraction."""
from __future__ import annotations
import os
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from spec.agent_contract import AgentResponse
from .state import AgentSession

load_dotenv()

# Use the standard client, we will use aio for async operations
client = genai.Client()

CHAT_PROMPT = """You are an expert, friendly AI Car Matchmaker assistant. 
Help the user find or rent a vehicle. Ask 1 or 2 natural questions at a time to uncover: intent (buy/rent), category, and budget.
Respond directly to the user in plain text. Keep it conversational and brief."""

STATE_PROMPT = """Analyze the conversation history and extract the current user preferences.
Set is_ready_for_recommendation to true ONLY if intent, category, and budget_max are known."""

async def stream_agent_reply(messages: list[dict]):
    """Track 1: Streams the plain text conversational reply."""
    formatted_contents = [
        types.Content(role="model" if m["role"] == "assistant" else "user", parts=[types.Part.from_text(text=m["content"])])
        for m in messages
    ]
    
    response = await client.aio.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=formatted_contents,
        config=types.GenerateContentConfig(system_instruction=CHAT_PROMPT, temperature=0.7)
    )
    
    async for chunk in response:
        if chunk.text:
            yield chunk.text

async def extract_state(messages: list[dict]) -> AgentResponse:
    """Track 2: Extracts the strict Pydantic JSON state from the conversation."""
    formatted_contents = [
        types.Content(role="model" if m["role"] == "assistant" else "user", parts=[types.Part.from_text(text=m["content"])])
        for m in messages
    ]
    
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=formatted_contents,
        config=types.GenerateContentConfig(
            system_instruction=STATE_PROMPT,
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=AgentResponse, 
        )
    )
    
    return AgentResponse.model_validate_json(response.text)