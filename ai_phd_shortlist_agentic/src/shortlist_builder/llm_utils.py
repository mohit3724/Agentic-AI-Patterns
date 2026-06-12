from __future__ import annotations

from typing import List

from .models import CandidateMatch


def generate_why_match(candidate: CandidateMatch) -> str:
    sup = candidate.supervisor
    student = candidate.student

    areas = ", ".join(sup.areas) if sup.areas else sup.research_focus
    interests = ", ".join(student.areas_of_interest) or ", ".join(student.research_interests)

    evidence_titles: List[str] = [e.title for e in candidate.evidence]
    evidence_str = "; ".join(evidence_titles) if evidence_titles else "their recent work and programs"

    return (
        f"You are a strong match for {sup.name} at {sup.institution} in {sup.country}. "
        f"Your interests in {interests} overlap with their focus on {areas}. "
        f"You can reference {evidence_str} when reaching out about potential PhD opportunities."
    )
