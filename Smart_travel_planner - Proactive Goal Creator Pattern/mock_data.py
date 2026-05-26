"""
mock_data.py
Simulated context sources that replace real integrations.
In production these would be actual email/calendar/location APIs.
Each function returns realistic structured data, mirroring what
real detectors / tools would capture in the Proactive Goal Creator pattern.
"""

from datetime import date, timedelta


def get_forwarded_email() -> dict:
    """Simulates a forwarded travel confirmation email."""
    return {
        "source": "email",
        "raw_text": (
            "---------- Forwarded message ----------\n"
            "From: bookings@travelco.com\n"
            "Subject: Your Booking Confirmation – Singapore Tech Summit 2026\n\n"
            "Dear Traveler,\n"
            "We are pleased to confirm your registration for Singapore Tech Summit 2026.\n"
            "Event Dates : 18 July 2026 – 20 July 2026\n"
            "Venue        : Marina Bay Sands Convention Centre, Singapore\n"
            "Reference    : STS2026-VJW-00847\n\n"
            "Your accommodation shortlist (not yet booked):\n"
            "  • JW Marriott South Beach, Singapore\n"
            "  • ibis budget Singapore\n\n"
            "Please ensure your visa and travel documents are in order.\n"
        ),
        "attachments": ["booking_confirmation.pdf"],
    }


def get_calendar_events() -> list[dict]:
    """Simulates calendar entries near the trip window."""
    base = date(2026, 7, 14)
    return [
        {
            "title": "Approved Leave – July",
            "start": "2026-07-17",
            "end": "2026-07-23",
            "type": "out_of_office",
        },
        {
            "title": "Sprint Review",
            "start": "2026-07-16",
            "end": "2026-07-16",
            "type": "meeting",
        },
        {
            "title": "Singapore Tech Summit – Day 1",
            "start": "2026-07-18",
            "end": "2026-07-18",
            "type": "conference",
        },
        {
            "title": "Singapore Tech Summit – Day 2",
            "start": "2026-07-19",
            "end": "2026-07-19",
            "type": "conference",
        },
        {
            "title": "Singapore Tech Summit – Day 3",
            "start": "2026-07-20",
            "end": "2026-07-20",
            "type": "conference",
        },
        {
            "title": "Return Flight Buffer",
            "start": "2026-07-21",
            "end": "2026-07-22",
            "type": "personal",
        },
    ]


def get_current_location() -> dict:
    """Simulates current device / profile location."""
    return {
        "city": "Vijayawada",
        "state": "Andhra Pradesh",
        "country": "India",
        "nearest_airport": "VGA",
        "hub_airports": ["HYD", "MAA", "BLR"],
        "timezone": "Asia/Kolkata",
    }


def get_passport_info() -> dict:
    """Simulates passport / nationality metadata from a user profile."""
    return {
        "nationality": "Indian",
        "passport_country_code": "IN",
        "passport_expiry": "2031-03-15",
        "requires_visa_for": ["Singapore", "Japan", "USA", "UK"],
        "visa_on_arrival": [],
        "known_visas": [
            {"country": "Singapore", "type": "e-Visa", "status": "not_obtained"}
        ],
    }


def get_budget_history() -> dict:
    """Simulates past travel spending patterns from the user's history."""
    return {
        "past_trips": [
            {
                "destination": "Bengaluru",
                "year": 2025,
                "flight_spend_inr": 4500,
                "hotel_per_night_inr": 3200,
                "hotel_tier": "3-star",
                "trip_type": "business",
            },
            {
                "destination": "Mumbai",
                "year": 2025,
                "flight_spend_inr": 5200,
                "hotel_per_night_inr": 4800,
                "hotel_tier": "4-star",
                "trip_type": "business",
            },
            {
                "destination": "Goa",
                "year": 2024,
                "flight_spend_inr": 6100,
                "hotel_per_night_inr": 5500,
                "hotel_tier": "4-star",
                "trip_type": "leisure",
            },
        ],
        "avg_hotel_per_night_inr": 4500,
        "avg_flight_inr": 5267,
        "preferred_hotel_tier": "4-star",
        "budget_band": "mid",
    }


def get_travel_preferences() -> dict:
    """Simulates remembered user preferences from past interactions."""
    return {
        "flight": {
            "seat": "aisle",
            "max_layovers": 1,
            "preferred_departure_time": "morning",
            "airlines_preferred": ["IndiGo", "Air India", "Singapore Airlines"],
        },
        "hotel": {
            "breakfast_included": True,
            "near": "conference_venue",
            "room_type": "king",
        },
        "general": {
            "trip_pace": "efficient",
            "currency": "INR",
            "dietary": "vegetarian",
        },
    }
