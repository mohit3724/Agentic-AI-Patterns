# Architecture: Smart Travel Planner — Proactive Goal Creator Pattern

## Pattern Applied
**Proactive Goal Creator** (from the FM-Based Agent Design Pattern Catalogue)

> "Proactive Goal Creator anticipates users' goals by understanding human
>  interactions and capturing the context via relevant tools."

## Why This Is a Strong Fit
Travel planning suffers from underspecified prompts. "Plan this trip" lacks
destination, dates, budget, and constraints. The Proactive Goal Creator solves
this by proactively pulling context from tools (email, calendar, location,
passport, budget history) before any planning begins.

## Agent Pipeline

```
User: "Plan this trip"
          │
          ▼
┌─────────────────────────────────────────────────────┐
│  STEP 1: ProactiveGoalCreatorAgent                  │
│  [Proactive Goal Creator Pattern]                   │
│                                                     │
│  Tools called (context detectors):                  │
│   ├── read_forwarded_email  → destination clue      │
│   ├── read_calendar_events → travel window          │
│   ├── get_user_location    → departure city/airport │
│   ├── get_passport_info    → visa requirements      │
│   ├── get_budget_history   → budget band            │
│   └── get_travel_preferences → hotel/flight prefs  │
│                                                     │
│  Output: InferredGoal JSON (structured goal object) │
│          with confidence scores + assumptions       │
└─────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────┐
│  STEP 2: GuardrailAgent                             │
│  [Multimodal Guardrails Pattern]                    │
│                                                     │
│  Validates: safety, feasibility, visa alerts,       │
│  date sanity, budget realism, consent markers       │
│                                                     │
│  Output: GuardrailResult (passed/blocked + issues)  │
│  ⚠ Blocks pipeline if hard issues found             │
└─────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────┐
│  STEP 3: TravelPlannerAgent                         │
│  [Multi-Path Plan Generator Pattern]                │
│                                                     │
│  Generates:                                         │
│   ├── 3 flight options (cheapest/balanced/fastest)  │
│   ├── 3 hotel options (budget/mid/premium)          │
│   ├── Day-by-day plan for entire trip window        │
│   ├── Visa checklist (if required)                  │
│   └── Packing tips + total cost estimate            │
│                                                     │
│  Output: TravelItinerary JSON                       │
└─────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────┐
│  STEP 4: ReflectionAgent                            │
│  [Self-Reflection Pattern]                          │
│                                                     │
│  Reviews: itinerary vs inferred goal                │
│  Checks: date consistency, budget alignment,        │
│          visa addressed, day plan completeness      │
│                                                     │
│  Output: ReflectionResult (approved/revision +      │
│          issues + suggestions)                      │
└─────────────────────────────────────────────────────┘
          │
          ▼
    Formatted console output (rich)
```

## File Structure
```
smart_travel_planner/
├── main.py            Entry point
├── pipeline.py        Orchestrator — runs all 4 agents in sequence
├── agents.py          Agent definitions using Agno + Gemini
├── tools.py           Agno function tools (context detectors)
├── models.py          Pydantic data models for structured artefacts
├── mock_data.py       Simulated context sources (email/calendar/etc.)
├── config.py          API key + model name configuration
├── requirements.txt   Python dependencies
├── .env.example       Environment variable template
└── ARCHITECTURE.md    This file
```

## Models Used (Gemini Free Tier)
| Agent              | Model                  | Reason                          |
|--------------------|------------------------|---------------------------------|
| Goal Creator       | gemini-2.0-flash       | Strong reasoning for inference  |
| Guardrail          | gemini-2.0-flash-lite  | Fast validation, lower cost     |
| Travel Planner     | gemini-2.0-flash       | Rich content generation         |
| Reflection         | gemini-2.0-flash-lite  | Efficient coherence checking    |

## Running
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
python main.py
# or
python main.py "Plan this trip"
```
