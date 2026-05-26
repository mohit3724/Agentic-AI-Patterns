"""
agents.py
Defines all four Agno agents that implement the Proactive Goal Creator pattern
for the Smart Travel Planner use case.

Agent pipeline (pattern-annotated):
  1. ProactiveGoalCreatorAgent  — [Proactive Goal Creator]
     Reads the vague user request, autonomously calls all context tools,
     synthesises them into a structured InferredGoal JSON.

  2. GuardrailAgent             — [Multimodal Guardrails]
     Validates the inferred goal for safety, feasibility, and consent issues
     before any planning begins.

  3. TravelPlannerAgent         — [Multi-Path Plan Generator]
     Receives the validated InferredGoal and generates a full TravelItinerary
     with multiple flight/hotel options plus a day-by-day plan.

  4. ReflectionAgent            — [Self-Reflection]
     Reviews the complete itinerary against the original goal for coherence,
     flags issues, and approves or requests revision.
"""

import json
from agno.agent import Agent
from agno.models.google import Gemini
from config import GEMINI_FAST_MODEL, GEMINI_SMART_MODEL, GOOGLE_API_KEY
from tools import (
    read_forwarded_email,
    read_calendar_events,
    get_user_location,
    get_passport_and_visa_info,
    get_budget_history_tool,
    get_travel_preferences_tool,
)

# ── 1. Proactive Goal Creator Agent ─────────────────────────────────────────

GOAL_CREATOR_INSTRUCTIONS = """
You are the Proactive Goal Creator for a Smart Travel Planner system.

Your job is to handle a vague user request like "Plan this trip" by proactively
gathering context from all available tools and converting it into a structured,
machine-usable InferredGoal JSON object.

STEPS YOU MUST FOLLOW:
1. Acknowledge the underspecified request.
2. Call ALL of the following tools (in any order) to gather context:
   - read_forwarded_email
   - read_calendar_events
   - get_user_location
   - get_passport_and_visa_info
   - get_budget_history
   - get_travel_preferences
3. Analyse ALL tool outputs together.
4. Infer: destination, travel_window (dates), departure_city, hub_airport,
   trip_type, budget_band, estimated_budget_inr, preferences, visa_required,
   visa_status, assumptions, missing_fields, and confidence scores (0.0–1.0).
5. Return ONLY a valid JSON object matching this schema exactly:

{
  "destination": "<city, country>",
  "travel_window": {
    "departure_date": "YYYY-MM-DD",
    "return_date": "YYYY-MM-DD",
    "flexibility_days": <int>,
    "note": "<any note>"
  },
  "departure_city": "<city>",
  "hub_airport": "<IATA code>",
  "trip_type": "<business|leisure|mixed>",
  "budget_band": "<economy|mid|premium>",
  "estimated_budget_inr": "<e.g. ₹85,000–₹1,10,000>",
  "preferences": {
    "flight": ["<pref1>", "<pref2>"],
    "hotel": ["<pref1>", "<pref2>"],
    "transport": ["<pref1>"],
    "dietary": "<value>",
    "pace": "<efficient|relaxed|intensive>"
  },
  "confidence": {
    "destination": <float>,
    "travel_window": <float>,
    "budget_band": <float>,
    "trip_type": <float>
  },
  "missing_fields": ["<field1>"],
  "assumptions": ["<assumption1>", "<assumption2>"],
  "visa_required": <true|false>,
  "visa_status": "<not_obtained|obtained|not_required>"
}

Return ONLY the JSON. No markdown fences, no explanation text.
"""

def build_goal_creator_agent() -> Agent:
    return Agent(
        name="ProactiveGoalCreatorAgent",
        model=Gemini(id=GEMINI_SMART_MODEL, api_key=GOOGLE_API_KEY),
        tools=[
            read_forwarded_email,
            read_calendar_events,
            get_user_location,
            get_passport_and_visa_info,
            get_budget_history_tool,
            get_travel_preferences_tool,
        ],
        instructions=GOAL_CREATOR_INSTRUCTIONS,
        markdown=False,
    )


# ── 2. Guardrail Agent ───────────────────────────────────────────────────────

GUARDRAIL_INSTRUCTIONS = """
You are the Guardrail Agent for a Smart Travel Planner.

You receive an InferredGoal JSON and must validate it for:
  - Safety: no harmful, illegal, or unethical travel goals.
  - Feasibility: dates are in the future, passport not expired before travel,
    budget is realistic for the destination.
  - Completeness: critical fields (destination, dates, departure) are present.
  - Consent markers: ensure no PII is improperly exposed.
  - Visa alerts: flag if visa is required but not obtained.

Return ONLY a valid JSON object with this schema:
{
  "passed": <true|false>,
  "issues": ["<blocker1>"],
  "warnings": ["<warning1>"],
  "redacted_fields": ["<field_name_if_any>"]
}

Return ONLY the JSON. No explanation.
"""

def build_guardrail_agent() -> Agent:
    return Agent(
        name="GuardrailAgent",
        model=Gemini(id=GEMINI_FAST_MODEL, api_key=GOOGLE_API_KEY),
        instructions=GUARDRAIL_INSTRUCTIONS,
        markdown=False,
    )


# ── 3. Travel Planner Agent (Multi-Path Plan Generator) ──────────────────────

PLANNER_INSTRUCTIONS = """
You are a Senior Travel Planner Agent using the Multi-Path Plan Generator pattern.

You receive a validated InferredGoal JSON and must generate a complete TravelItinerary.

RULES:
- Generate exactly 3 flight options (cheapest, balanced, fastest).
- Generate exactly 3 hotel options (budget, mid-range, premium).
- Recommend one flight and one hotel with a clear reason.
- Generate a day-by-day plan for each day of the trip window (morning/afternoon/evening).
- Include a visa checklist if visa_required is true.
- Include 5 packing tips relevant to the destination and trip type.
- Provide a total estimated cost in INR.
- Note all assumptions made.

Return ONLY a valid JSON object matching this schema:
{
  "goal_summary": "<one sentence summary>",
  "flight_options": [
    {
      "option_label": "Option A – Cheapest",
      "route": "<VGA/HYD → SIN>",
      "airline": "<name>",
      "departure_time": "<HH:MM>",
      "arrival_time": "<HH:MM>",
      "stops": <int>,
      "estimated_cost_inr": "<e.g. ₹22,000>",
      "notes": "<note>"
    }
  ],
  "hotel_options": [
    {
      "option_label": "Option 1 – Budget",
      "hotel_name": "<name>",
      "tier": "<3-star>",
      "distance_to_venue": "<e.g. 1.2 km>",
      "estimated_cost_per_night_inr": "<e.g. ₹8,500>",
      "total_nights": <int>,
      "includes_breakfast": <true|false>,
      "notes": "<note>"
    }
  ],
  "recommended_flight": "Option A – Cheapest",
  "recommended_hotel": "Option 2 – Mid-Range",
  "day_plans": [
    {
      "date": "YYYY-MM-DD",
      "morning": "<activity>",
      "afternoon": "<activity>",
      "evening": "<activity>",
      "transport_note": "<note>"
    }
  ],
  "visa_checklist": {
    "required": true,
    "type": "e-Visa",
    "estimated_processing_days": 3,
    "documents_needed": ["Passport copy", "Photo", "Travel itinerary", "Bank statement"],
    "apply_url": "https://eservices.ica.gov.sg"
  },
  "packing_tips": ["<tip1>", "<tip2>", "<tip3>", "<tip4>", "<tip5>"],
  "total_estimated_cost_inr": "<range>",
  "assumptions_noted": ["<assumption1>"]
}

Return ONLY the JSON. No markdown fences, no explanation.
"""

def build_planner_agent() -> Agent:
    return Agent(
        name="TravelPlannerAgent",
        model=Gemini(id=GEMINI_SMART_MODEL, api_key=GOOGLE_API_KEY),
        instructions=PLANNER_INSTRUCTIONS,
        markdown=False,
    )


# ── 4. Reflection Agent (Self-Reflection) ────────────────────────────────────

REFLECTION_INSTRUCTIONS = """
You are the Reflection Agent implementing the Self-Reflection pattern.

You receive TWO JSON objects:
  1. inferred_goal  — the InferredGoal produced by the Proactive Goal Creator.
  2. itinerary      — the TravelItinerary produced by the Planner.

Your job is to:
  - Check that the itinerary destination matches the inferred goal.
  - Check that travel dates are consistent across goal and itinerary.
  - Check that recommended options are within the stated budget band.
  - Check that visa requirements are addressed if visa_required=true.
  - Check that day plans cover every day of the travel window.
  - Identify any hallucinated facts, inconsistencies, or missing critical items.
  - Suggest improvements (maximum 5 actionable suggestions).
  - Decide whether to APPROVE or REQUEST REVISION.

Return ONLY a valid JSON object:
{
  "coherent": <true|false>,
  "issues_found": ["<issue1>"],
  "suggestions": ["<suggestion1>"],
  "confidence_adjustment": {
    "destination": <float delta e.g. +0.02>,
    "travel_window": <float delta>,
    "budget_band": <float delta>
  },
  "approved": <true|false>,
  "final_note": "<one sentence summary>"
}

Return ONLY the JSON. No explanation.
"""

def build_reflection_agent() -> Agent:
    return Agent(
        name="ReflectionAgent",
        model=Gemini(id=GEMINI_FAST_MODEL, api_key=GOOGLE_API_KEY),
        instructions=REFLECTION_INSTRUCTIONS,
        markdown=False,
    )
