from __future__ import annotations

import json
from typing import Any, Dict, List

from .models import (
    StudentProfile,
    EducationEntry,
    ProjectEntry,
    PublicationEntry,
    TargetIntake,
)


def _normalise_interest(interest: str) -> str:
    return interest.strip().lower()


def _derive_areas_of_interest(research_interests: List[str]) -> List[str]:
    seen = set()
    areas: List[str] = []
    for r in research_interests:
        norm = _normalise_interest(r)
        if norm and norm not in seen:
            seen.add(norm)
            areas.append(norm)
    return areas


def load_student_profile(path: str) -> StudentProfile:
    with open(path, "r", encoding="utf-8") as f:
        raw: Dict[str, Any] = json.load(f)

    education_history = [
        EducationEntry(
            degree=e.get("degree", ""),
            field=e.get("field"),
            institution=e.get("institution"),
            grade=e.get("grade"),
            thesis_title=e.get("thesis_title"),
            year=e.get("year"),
        )
        for e in raw.get("education_history", [])
    ]

    projects = [
        ProjectEntry(title=p.get("title", ""), description=p.get("description"))
        for p in raw.get("projects", [])
    ]

    publications = [
        PublicationEntry(
            title=p.get("title", ""),
            venue=p.get("venue"),
            year=p.get("year"),
        )
        for p in raw.get("publications", [])
    ]

    ti_raw = raw.get("target_intake") or {}
    target_intake = None
    if ti_raw:
        target_intake = TargetIntake(
            semester=ti_raw.get("semester"),
            year=ti_raw.get("year"),
        )

    profile = StudentProfile(
        student_id=str(raw.get("student_id", "unknown")),
        education_history=education_history,
        skills=list(raw.get("skills", [])),
        projects=projects,
        publications=publications,
        research_interests=list(raw.get("research_interests", [])),
        target_countries=list(raw.get("target_countries", [])),
        target_intake=target_intake,
        intro_call_summary=raw.get("intro_call_summary"),
        raw_resume_text=raw.get("raw_resume_text"),
    )

    profile.areas_of_interest = _derive_areas_of_interest(profile.research_interests)
    return profile
