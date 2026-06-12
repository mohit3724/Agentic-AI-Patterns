from __future__ import annotations

from typing import List

from .models import CandidateMatch


def _topic_similarity(candidate: CandidateMatch) -> float:
    student_areas = set(candidate.student.areas_of_interest)
    sup_areas = set(a.lower() for a in candidate.supervisor.areas)
    if not student_areas or not sup_areas:
        return 0.0
    inter = len(student_areas & sup_areas)
    union = len(student_areas | sup_areas)
    return inter / union


def _recent_activity_score(candidate: CandidateMatch) -> float:
    return 0.7


def _availability_score(candidate: CandidateMatch) -> float:
    return 0.9 if candidate.programs else 0.5


def score_and_tier(candidates: List[CandidateMatch]) -> List[CandidateMatch]:
    for c in candidates:
        topic = _topic_similarity(c)
        recent = _recent_activity_score(c)
        avail = _availability_score(c)
        overall = 0.6 * topic + 0.2 * recent + 0.2 * avail
        c.scores["topic_similarity"] = topic
        c.scores["recent_activity"] = recent
        c.scores["availability"] = avail
        c.scores["overall"] = overall

    candidates.sort(key=lambda c: c.scores["overall"], reverse=True)

    n = len(candidates)
    for idx, c in enumerate(candidates):
        pct = (idx + 1) / max(n, 1)
        if pct <= 0.2:
            tier = "reach"
        elif pct <= 0.7:
            tier = "target"
        else:
            tier = "safety"
        c.tier = tier

    return candidates
