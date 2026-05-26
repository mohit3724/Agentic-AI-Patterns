"""
tools.py
Agno Function tools — each tool wraps one context source.
These are registered on the Proactive Goal Creator agent so that
it can call them autonomously to gather multimodal context,
exactly as described in the Proactive Goal Creator pattern:
  "sending requirements to detectors, which will then capture
   and return the user's surroundings with multimodal context
   information for further analysis."
"""

import json
from agno.tools import tool
from mock_data import (
    get_forwarded_email,
    get_calendar_events,
    get_current_location,
    get_passport_info,
    get_budget_history,
    get_travel_preferences,
)


@tool(name="read_forwarded_email",
      description=(
          "Reads the most recently forwarded travel confirmation or booking email "
          "from the user's inbox. Returns raw email text and attachment list."
      ))
def read_forwarded_email() -> str:
    data = get_forwarded_email()
    return json.dumps(data, indent=2)


@tool(name="read_calendar_events",
      description=(
          "Reads upcoming calendar events for the next 60 days including leave blocks, "
          "meetings, and any travel-related entries. Returns a list of event objects."
      ))
def read_calendar_events() -> str:
    data = get_calendar_events()
    return json.dumps(data, indent=2)


@tool(name="get_user_location",
      description=(
          "Returns the user's current city, country, nearest airport code, "
          "and nearby hub airports that support international routes."
      ))
def get_user_location() -> str:
    data = get_current_location()
    return json.dumps(data, indent=2)


@tool(name="get_passport_and_visa_info",
      description=(
          "Returns the user's nationality, passport expiry, and a list of countries "
          "that require a visa for this user. Also returns any known/obtained visas."
      ))
def get_passport_and_visa_info() -> str:
    data = get_passport_info()
    return json.dumps(data, indent=2)


@tool(name="get_budget_history",
      description=(
          "Returns the user's past travel spending history including average flight cost, "
          "average hotel tier and nightly rate, and inferred budget band (economy/mid/premium)."
      ))
def get_budget_history_tool() -> str:
    data = get_budget_history()
    return json.dumps(data, indent=2)


@tool(name="get_travel_preferences",
      description=(
          "Returns the user's remembered travel preferences: preferred airlines, "
          "seat type, hotel amenities, dietary requirements, and trip pace."
      ))
def get_travel_preferences_tool() -> str:
    data = get_travel_preferences()
    return json.dumps(data, indent=2)
