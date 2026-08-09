"""Core data model for the AI Car Matchmaker agent.

Everything the agent knows about a session lives in one AgentSession object,
which is what gets serialized to disk / memory store and streamed to the
frontend as A2UI updates.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid
import time


class Stage(str, Enum):
    INTERVIEW = "interview"
    RESEARCH = "research"
    RECOMMEND = "recommend"
    FORM = "form"
    PAYMENT = "payment"
    DONE = "done"


class UserPreferences(BaseModel):
    intent: Optional[str] = None          # "buy" | "rent"
    use_case: Optional[str] = None        # "commuting", "family road trip", ...
    category: Optional[str] = None        # "SUV", "Sedan", "Hatchback", ...
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    target_date: Optional[str] = None     # ISO date - when they need the car
    seats: Optional[int] = None
    location: Optional[str] = None
    fuel_type: Optional[str] = None       # "petrol" | "diesel" | "electric" | "hybrid"

    def missing_fields(self) -> list[str]:
        required = ["intent", "use_case", "category", "budget_max", "target_date"]
        return [f for f in required if getattr(self, f) in (None, "")]


class CarListing(BaseModel):
    id: str
    brand: str
    model: str
    category: str
    year: int
    price: float                 # sale price OR price-per-day for rentals
    intent: str                  # "buy" | "rent"
    mileage_km: int
    condition: str               # "new" | "used" | "certified"
    seats: int
    fuel_type: str
    location: str
    available_from: str          # ISO date
    dealer: str
    image_seed: str = ""


class RankedListing(BaseModel):
    listing: CarListing
    score: float
    explanation: str


class ReasoningStep(BaseModel):
    ts: float = Field(default_factory=time.time)
    text: str


class AgentSession(BaseModel):
    session_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    stage: Stage = Stage.INTERVIEW
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    reasoning_log: list[ReasoningStep] = Field(default_factory=list)
    results: list[RankedListing] = Field(default_factory=list)
    selected_listing_id: Optional[str] = None
    booking_form: Optional[dict] = None
    payment_status: Optional[str] = None  # "pending" | "confirmed"
    updated_at: float = Field(default_factory=time.time)

    def log(self, text: str) -> None:
        self.reasoning_log.append(ReasoningStep(text=text))
        self.updated_at = time.time()