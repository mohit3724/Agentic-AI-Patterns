# Smart Travel Planner — Proactive Goal Creator Pattern
## Built with Agno + Gemini Free Tier (Python)

---

## What This Project Does

A user says **"Plan this trip"** — nothing else.

Instead of asking 10 clarifying questions, the agent system **proactively
reads** a forwarded confirmation email, checks the calendar, detects current
location, inspects passport/nationality, and reads budget history and saved
preferences. It then converts that underspecified request into a fully
structured travel itinerary — complete with flight options, hotel options,
a day-by-day plan, a visa checklist, and a packing list.

This is a real-world implementation of the **Proactive Goal Creator** design
pattern from the FM-Based Agent Design Pattern Catalogue.

---

## Folder Structure

```
smart_travel_planner/
│
├── main.py              ← Entry point. Run this.
├── pipeline.py          ← Orchestrates all 4 agents end-to-end
├── agents.py            ← All 4 Agno agent definitions with system prompts
├── tools.py             ← 6 Agno @tool context detectors (email, calendar, etc.)
├── models.py            ← Pydantic data models for all JSON contracts
├── mock_data.py         ← Simulated data sources (replaces real APIs)
├── config.py            ← API key + Gemini model name configuration
├── requirements.txt     ← Python dependencies
├── .env.example         ← Template for your environment variables
├── README.md            ← This file
└── ARCHITECTURE.md      ← Deep-dive architecture and pattern mapping
```

---

## Agent Pipeline (4 Agents)

```
User: "Plan this trip"
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 1 — ProactiveGoalCreatorAgent                           │
│  Pattern : Proactive Goal Creator                              │
│  Model   : gemini-2.0-flash                                    │
│                                                                 │
│  Calls 6 tools autonomously:                                   │
│    read_forwarded_email   → destination, event dates, venue    │
│    read_calendar_events   → travel window, hard constraints    │
│    get_user_location      → departure city & hub airport       │
│    get_passport_and_visa_info → visa requirements              │
│    get_budget_history     → budget band, spending patterns     │
│    get_travel_preferences → airlines, hotel, dietary, pace     │
│                                                                 │
│  Output: InferredGoal JSON with confidence scores              │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 2 — GuardrailAgent                                      │
│  Pattern : Multimodal Guardrails                               │
│  Model   : gemini-2.0-flash-lite                               │
│                                                                 │
│  Validates: safety, feasibility, date sanity, visa alerts,     │
│  passport expiry, consent markers                              │
│                                                                 │
│  Output: GuardrailResult (passed/blocked + issues + warnings)  │
│  ⛔ Halts pipeline if hard issues are found                     │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 3 — TravelPlannerAgent                                  │
│  Pattern : Multi-Path Plan Generator                           │
│  Model   : gemini-2.0-flash                                    │
│                                                                 │
│  Generates:                                                     │
│    • 3 flight options (cheapest / balanced / fastest)          │
│    • 3 hotel options (budget / mid-range / premium)            │
│    • Day-by-day itinerary (morning / afternoon / evening)      │
│    • Visa checklist (if required)                              │
│    • 5 packing tips + total cost estimate                      │
│                                                                 │
│  Output: TravelItinerary JSON                                  │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 4 — ReflectionAgent                                     │
│  Pattern : Self-Reflection                                     │
│  Model   : gemini-2.0-flash-lite                               │
│                                                                 │
│  Reviews itinerary vs inferred goal:                           │
│    • Destination match                                         │
│    • Date consistency across all day plans                     │
│    • Budget alignment with budget_band                         │
│    • Visa checklist present if required                        │
│    • Day plans cover every day in travel window                │
│                                                                 │
│  Output: ReflectionResult (approved / revision + suggestions)  │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
   Formatted rich console output
```

---

## Design Patterns Used

| Agent | Pattern (from Catalogue) | Purpose |
|---|---|---|
| ProactiveGoalCreatorAgent | Proactive Goal Creator | Infer structured goal from weak input |
| GuardrailAgent | Multimodal Guardrails | Safety & feasibility gate |
| TravelPlannerAgent | Multi-Path Plan Generator | Generate multiple options per decision |
| ReflectionAgent | Self-Reflection | Coherence check before final output |

---

## Models Used (All Free Tier)

| Agent | Model | Reason |
|---|---|---|
| Goal Creator | `gemini-2.0-flash` | Complex multi-tool reasoning |
| Guardrail | `gemini-2.0-flash-lite` | Fast rule-based validation |
| Planner | `gemini-2.0-flash` | Rich multi-option generation |
| Reflection | `gemini-2.0-flash-lite` | Efficient coherence checking |

Get your **free** API key at: https://aistudio.google.com/apikey

---

## Setup & Run

### Step 1 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 2 — Set your API key

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder:
```
GOOGLE_API_KEY=your_actual_gemini_api_key_here
```

### Step 3 — Run the planner

```bash
python main.py
```

Or pass a custom message:
```bash
python main.py "Plan this trip"
python main.py "Book my travel"
```

---

## What You Will See in the Console

The output is structured in 4 clearly labelled steps:

```
────────── STEP 1 — Proactive Goal Creator Agent ──────────
[Shows: Inferred Goal JSON + confidence score bars + assumptions]

────────── STEP 2 — Guardrail Agent ───────────────────────
[Shows: PASSED / BLOCKED + any warnings]

────────── STEP 3 — Travel Planner Agent ──────────────────
[Shows: Trip summary, 3 flight options, 3 hotel options,
        day-by-day plan, visa checklist, packing tips, cost]

────────── STEP 4 — Reflection Agent ──────────────────────
[Shows: APPROVED / REVISION REQUESTED + issues + suggestions]

────────── Pipeline Complete ───────────────────────────────
[Shows: Final summary card]
```

---

## Extending to Production

| Mock component | Real replacement |
|---|---|
| `get_forwarded_email()` | Gmail API / Outlook Graph API |
| `get_calendar_events()` | Google Calendar API / Exchange API |
| `get_current_location()` | Device GPS API / IP geolocation |
| `get_passport_info()` | User profile DB / identity vault |
| `get_budget_history()` | Expense management system / bank API |
| `get_travel_preferences()` | User preferences DB / CRM |

---

## Key Design Decisions

1. **All agent outputs are Pydantic-validated JSON** — no free-form text
   leaks into downstream agents. Every agent contract is enforced by a model.

2. **Confidence scores are first-class outputs** — the goal creator always
   reports how certain it is about each inferred field, and the reflection
   agent can adjust these scores after cross-checking.

3. **Guardrail halts the entire pipeline** — if visa dates, passport expiry,
   or safety checks fail, no itinerary is generated.

4. **Assumptions are always surfaced to the user** — the agent never silently
   assumes. Every inference is logged and shown.

5. **Two Gemini models, free tier only** — `gemini-2.0-flash` for reasoning-
   heavy agents and `gemini-2.0-flash-lite` for fast validation agents.

---

## File-by-File Guide

| File | Read when you want to... |
|---|---|
| `main.py` | Understand the entry point and CLI interface |
| `pipeline.py` | Understand how agents are orchestrated and output is displayed |
| `agents.py` | See the system prompts and model assignments for each agent |
| `tools.py` | See how context detectors are defined as Agno `@tool` functions |
| `models.py` | See the exact JSON contracts between all agents |
| `mock_data.py` | See the simulated context data and how to replace with real APIs |
| `config.py` | Change model names or add additional configuration |
| `ARCHITECTURE.md` | Read the full pattern-to-code mapping and design rationale |

---

## Requirements

- Python 3.11+
- Google Gemini API key (free tier)
- Internet connection (for Gemini API calls)
