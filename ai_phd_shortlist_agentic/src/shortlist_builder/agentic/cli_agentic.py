from __future__ import annotations

import argparse
import os

from .crew_runner import build_shortlist_agentic_to_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic PhD shortlist pipeline (CrewAI + LangSmith)")
    parser.add_argument("--input", required=True, help="Path to input student profile JSON")
    parser.add_argument("--output", required=True, help="Path to output shortlist JSON")
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Data directory containing supervisors.json and programs.json (defaults to ../data)",
    )
    args = parser.parse_args()

    if args.data_dir is None:
        here = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.abspath(os.path.join(here, os.pardir, os.pardir, "data"))
    else:
        data_dir = args.data_dir

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    build_shortlist_agentic_to_json(args.input, data_dir=data_dir, output_path=args.output)


if __name__ == "__main__":
    main()
