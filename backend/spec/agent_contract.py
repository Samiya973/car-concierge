"""Agent Output Contract.

Defines the exact JSON schema the Gemini LLM must return on every turn.
This eliminates string-parsing heuristics and guarantees type-safe state updates.
"""
from typing import Optional
from pydantic import BaseModel, Field


class ExtractedPreferences(BaseModel):
    intent: Optional[str] = Field(None, description="Strictly 'buy' or 'rent'.")
    use_case: Optional[str] = Field(None, description="E.g., daily commuting, family road trips, off-roading.")
    category: Optional[str] = Field(None, description="E.g., SUV, Sedan, Hatchback, Luxury SUV, Electric, etc.")
    budget_max: Optional[float] = Field(None, description="Maximum budget in INR (total price or daily rate).")
    target_date: Optional[str] = Field(None, description="ISO Date YYYY-MM-DD when the user needs the car.")
    seats: Optional[int] = Field(None, description="Minimum number of seats required.")
    location: Optional[str] = Field(None, description="City location of the user.")
    fuel_type: Optional[str] = Field(None, description="Strictly 'petrol', 'diesel', 'electric', or 'hybrid'.")


class AgentResponse(BaseModel):
    conversational_reply: str = Field(
        ..., 
        description="The natural language reply to the user. Must be engaging and conversational."
    )
    preferences: ExtractedPreferences = Field(
        ..., 
        description="The current state of all user preferences extracted from the ongoing chat history."
    )
    is_ready_for_recommendation: bool = Field(
        ..., 
        description="True ONLY if the core preferences (intent, category, and budget) are fully gathered."
    )