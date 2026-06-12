from __future__ import annotations

import os
from typing import List, Dict, Any

from ..models import CandidateMatch, Shortlist, shortlist_to_dict
from ..profile_ingestion import load_student_profile
from ..retrieval import get_candidate_supervisors
from ..ranking import score_and_tier
from ..llm_utils import generate_why_match


def load_profile_tool(input_path: str) -> Dict[str, Any]:
    profile = load_student_profile(input_path)
    return {
        "student_id": profile.student_id,
        "target_countries": profile.target_countries,
        "areas_of_interest": profile.areas_of_interest,
    }


def retrieve_candidates_tool(input_path: str, data_dir: str) -> List[CandidateMatch]:
    profile = load_student_profile(input_path)
    return get_candidate_supervisors(profile, data_dir=data_dir)


def validate_and_rank_tool(candidates: List[CandidateMatch]) -> List[CandidateMatch]:
    candidates = [c for c in candidates if c.supervisor.is_pi]
    return score_and_tier(candidates)


def generate_shortlist_tool(candidates: List[CandidateMatch], student_id: str, target_countries: list) -> Shortlist:
    for c in candidates:
        c.scores["why_match_text"] = generate_why_match(c)

    from datetime import datetime, timezone

    generated_at = datetime.now(timezone.utc).isoformat()
    return Shortlist(
        student_id=student_id,
        generated_at=generated_at,
        target_countries=target_countries,
        recommendations=candidates,
    )


def save_shortlist_json(shortlist: Shortlist, output_path: str) -> None:
    payload = shortlist_to_dict(shortlist)
    import json

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
