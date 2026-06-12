from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from .models import Shortlist, shortlist_to_dict, CandidateMatch
from .profile_ingestion import load_student_profile
from .retrieval import get_candidate_supervisors
from .ranking import score_and_tier
from .llm_utils import generate_why_match


def build_shortlist(input_path: str, data_dir: str) -> Shortlist:
    student = load_student_profile(input_path)
    candidates: List[CandidateMatch] = get_candidate_supervisors(student, data_dir=data_dir)
    candidates = [c for c in candidates if c.supervisor.is_pi]
    candidates = score_and_tier(candidates)

    for c in candidates:
        c.scores["why_match_text"] = generate_why_match(c)

    generated_at = datetime.now(timezone.utc).isoformat()
    return Shortlist(
        student_id=student.student_id,
        generated_at=generated_at,
        target_countries=student.target_countries,
        recommendations=candidates,
    )


def build_shortlist_to_json(input_path: str, data_dir: str, output_path: str) -> None:
    import json

    shortlist = build_shortlist(input_path, data_dir=data_dir)
    payload = shortlist_to_dict(shortlist)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
