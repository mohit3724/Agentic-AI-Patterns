"""
models.py
Pydantic data models representing the structured artefacts
produced and consumed by each agent in the pipeline.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


# ── Raw context bundle assembled by context-capture tools ───────────────────

class RawContext(BaseModel):
    email_text: str
    calendar_events: list[dict]
    location: dict
    passport_info: dict
    budget_history: dict
    travel_preferences: dict


# ── Inferred goal object produced by the Proactive Goal Creator ─────────────

class TravelWindow(BaseModel):
    departure_date: str
    return_date: str
    flexibility_days: int = 0
    note: str = ""


class InferredPreferences(BaseModel):
    flight: list[str] = Field(default_factory=list)
    hotel: list[str] = Field(default_factory=list)
    transport: list[str] = Field(default_factory=list)
    dietary: str = ""
    pace: str = "efficient"


class ConfidenceScores(BaseModel):
    destination: float
    travel_window: float
    budget_band: float
    trip_type: float


class InferredGoal(BaseModel):
    destination: str
    travel_window: TravelWindow
    departure_city: str
    hub_airport: str
    trip_type: str                    # business / leisure / mixed
    budget_band: str                  # economy / mid / premium
    estimated_budget_inr: str
    preferences: InferredPreferences
    confidence: ConfidenceScores
    missing_fields: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    visa_required: bool = False
    visa_status: str = ""


# ── Guardrail verdict ────────────────────────────────────────────────────────

class GuardrailResult(BaseModel):
    passed: bool
    issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    redacted_fields: list[str] = Field(default_factory=list)


# ── Itinerary options produced by the Planner agent ─────────────────────────

class FlightOption(BaseModel):
    option_label: str
    route: str
    airline: str
    departure_time: str
    arrival_time: str
    stops: int
    estimated_cost_inr: str
    notes: str = ""


class HotelOption(BaseModel):
    option_label: str
    hotel_name: str
    tier: str
    distance_to_venue: str
    estimated_cost_per_night_inr: str
    total_nights: int
    includes_breakfast: bool
    notes: str = ""


class DayPlan(BaseModel):
    date: str
    morning: str
    afternoon: str
    evening: str
    transport_note: str = ""


class VisaChecklist(BaseModel):
    required: bool
    type: str
    estimated_processing_days: int
    documents_needed: list[str]
    apply_url: str = ""


class TravelItinerary(BaseModel):
    goal_summary: str
    flight_options: list[FlightOption]
    hotel_options: list[HotelOption]
    recommended_flight: str
    recommended_hotel: str
    day_plans: list[DayPlan]
    visa_checklist: Optional[VisaChecklist] = None
    packing_tips: list[str] = Field(default_factory=list)
    total_estimated_cost_inr: str = ""
    assumptions_noted: list[str] = Field(default_factory=list)


# ── Reflection verdict produced by the Reflection agent ─────────────────────

class ReflectionResult(BaseModel):
    coherent: bool
    issues_found: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    confidence_adjustment: dict = Field(default_factory=dict)
    approved: bool = False
    final_note: str = ""
