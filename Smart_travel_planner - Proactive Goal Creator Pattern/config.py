"""
config.py
Central configuration for the Smart Travel Planner.
Set GOOGLE_API_KEY in a .env file or as an environment variable.
Uses Gemini free-tier models only.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Gemini free-tier model identifiers ──────────────────────────────────────
# gemini-2.0-flash-lite : fastest, cheapest, good for extraction tasks
# gemini-2.0-flash      : stronger reasoning, still free tier
# gemini-1.5-flash      : fallback option
GEMINI_FAST_MODEL   = "gemini-3.1-flash-lite"   # context extractors, guardrails
GEMINI_SMART_MODEL  = "gemini-3.5-flash"         # goal creator, planner, reflector

GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise EnvironmentError(
        "GOOGLE_API_KEY is not set. "
        "Create a .env file with GOOGLE_API_KEY=<your_key> "
        "or export it as an environment variable."
    )
