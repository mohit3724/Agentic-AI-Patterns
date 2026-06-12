from __future__ import annotations

import json
import os
from typing import List, Dict, Any

from .models import StudentProfile, Supervisor, Program, Eligibility, EvidenceItem, CandidateMatch


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_supervisors(data_dir: str) -> List[Supervisor]:
    path = os.path.join(data_dir, "supervisors.json")
    raw = _load_json(path)
    supervisors: List[Supervisor] = []
    for s in raw:
        supervisors.append(
            Supervisor(
                supervisor_id=s["supervisor_id"],
                name=s["name"],
                institution=s["institution"],
                department=s.get("department"),
                country=s["country"],
                email=s.get("email"),
                website=s.get("website"),
                research_focus=s.get("research_focus", ""),
                areas=list(s.get("areas", [])),
                is_pi=bool(s.get("is_pi", True)),
            )
        )
    return supervisors


def load_programs(data_dir: str) -> List[Program]:
    path = os.path.join(data_dir, "programs.json")
    raw = _load_json(path)
    programs: List[Program] = []
    for p in raw:
        elig_raw: Dict[str, Any] = p.get("eligibility", {})
        eligibility = Eligibility(
            citizenship=elig_raw.get("citizenship", "open"),
            allowed_countries=list(elig_raw.get("allowed_countries", [])),
            notes=elig_raw.get("notes"),
        )
        programs.append(
            Program(
                program_id=p["program_id"],
                name=p["name"],
                url=p["url"],
                intake=p.get("intake"),
                eligibility=eligibility,
            )
        )
    return programs


def is_program_eligible_for_student(program: Program, student: StudentProfile) -> bool:
    if program.eligibility.citizenship == "open":
        return True
    return any(c in program.eligibility.allowed_countries for c in student.target_countries)


def get_candidate_supervisors(student: StudentProfile, data_dir: str) -> List[CandidateMatch]:
    supervisors = load_supervisors(data_dir)
    programs = load_programs(data_dir)

    candidates: List[CandidateMatch] = []

    for sup in supervisors:
        if student.target_countries and sup.country not in student.target_countries:
            continue

        sup_areas_lower = [a.lower() for a in sup.areas]
        overlap = any(a in sup_areas_lower for a in student.areas_of_interest)
        if not overlap:
            continue

        inst_programs = []
        for p in programs:
            if sup.institution.lower() in p.name.lower() and is_program_eligible_for_student(p, student):
                inst_programs.append(p)

        evidence: List[EvidenceItem] = []
        for p in inst_programs:
            evidence.append(
                EvidenceItem(
                    type="program",
                    title=p.name,
                    url=p.url,
                    year=None,
                )
            )

        candidates.append(
            CandidateMatch(
                student=student,
                supervisor=sup,
                programs=inst_programs,
                evidence=evidence,
            )
        )
    return candidates
