from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class EducationEntry:
    degree: str
    field: Optional[str] = None
    institution: Optional[str] = None
    grade: Optional[float] = None
    thesis_title: Optional[str] = None
    year: Optional[int] = None


@dataclass
class ProjectEntry:
    title: str
    description: Optional[str] = None


@dataclass
class PublicationEntry:
    title: str
    venue: Optional[str] = None
    year: Optional[int] = None


@dataclass
class TargetIntake:
    semester: Optional[str] = None
    year: Optional[int] = None


@dataclass
class StudentProfile:
    student_id: str
    education_history: List[EducationEntry] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    projects: List[ProjectEntry] = field(default_factory=list)
    publications: List[PublicationEntry] = field(default_factory=list)
    research_interests: List[str] = field(default_factory=list)
    target_countries: List[str] = field(default_factory=list)
    target_intake: Optional[TargetIntake] = None
    intro_call_summary: Optional[str] = None
    raw_resume_text: Optional[str] = None
    areas_of_interest: List[str] = field(default_factory=list)


@dataclass
class Eligibility:
    citizenship: str = "open"  # "open" or "restricted"
    allowed_countries: List[str] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass
class Program:
    program_id: str
    name: str
    url: str
    intake: Optional[str] = None
    eligibility: Eligibility = field(default_factory=Eligibility)


@dataclass
class EvidenceItem:
    type: str  # "paper", "grant", or "program"
    title: str
    url: str
    year: Optional[int] = None


@dataclass
class Supervisor:
    supervisor_id: str
    name: str
    institution: str
    department: Optional[str]
    country: str
    email: Optional[str]
    website: Optional[str]
    research_focus: str
    areas: List[str]
    is_pi: bool = True


@dataclass
class CandidateMatch:
    student: StudentProfile
    supervisor: Supervisor
    programs: List[Program] = field(default_factory=list)
    evidence: List[EvidenceItem] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    tier: Optional[str] = None


@dataclass
class Shortlist:
    student_id: str
    generated_at: str
    target_countries: List[str]
    recommendations: List[CandidateMatch]


def shortlist_to_dict(shortlist: Shortlist) -> Dict[str, Any]:
    def conv_candidate(c: CandidateMatch) -> Dict[str, Any]:
        return {
            "supervisor_id": c.supervisor.supervisor_id,
            "name": c.supervisor.name,
            "institution": c.supervisor.institution,
            "department": c.supervisor.department,
            "country": c.supervisor.country,
            "email": c.supervisor.email,
            "website": c.supervisor.website,
            "research_focus": c.supervisor.research_focus,
            "areas": c.supervisor.areas,
            "tier": c.tier,
            "scores": c.scores,
            "evidence": [asdict(e) for e in c.evidence],
            "programs": [
                {
                    "name": p.name,
                    "url": p.url,
                    "intake": p.intake,
                    "eligibility": {
                        "citizenship": p.eligibility.citizenship,
                        "allowed_countries": p.eligibility.allowed_countries,
                        "notes": p.eligibility.notes,
                    },
                }
                for p in c.programs
            ],
            "why_match": c.scores.get("why_match_text", ""),
        }

    return {
        "student_id": shortlist.student_id,
        "generated_at": shortlist.generated_at,
        "target_countries": shortlist.target_countries,
        "recommendations": [conv_candidate(c) for c in shortlist.recommendations],
    }
