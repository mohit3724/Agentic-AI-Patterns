"""
main.py
Entry point for the Smart Travel Planner.

Usage:
    python main.py
    python main.py "Plan this trip"
    python main.py "Book my travel"

The agent handles any short underspecified trip-intent phrase.
"""

import sys
from pipeline import run_pipeline


def main():
    user_message = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else "Plan this trip"
    run_pipeline(user_message)


if __name__ == "__main__":
    main()
