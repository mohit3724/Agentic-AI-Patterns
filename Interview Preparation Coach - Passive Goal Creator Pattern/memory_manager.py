"""
memory_manager.py
=================
Persistent JSON-based memory store for the Interview Preparation Coach.
Implements the memory retrieval step in the Passive Goal Creator pattern:
  - Stores topics covered, weak areas, Q&A history, and feedback
  - Loaded by the Goal Interpreter Agent before planning
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

MEMORY_FILE = os.getenv("MEMORY_FILE", "./data/memory_store.json")


def _ensure_dir():
    Path(MEMORY_FILE).parent.mkdir(parents=True, exist_ok=True)


def load_memory() -> dict:
    """Load full memory from disk. Returns empty structure if not found."""
    _ensure_dir()
    if Path(MEMORY_FILE).exists():
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {
        "topics_covered": [],       # list of topic strings already prepared
        "weak_areas": [],           # list of topics flagged as weak
        "questions_seen": {},       # topic -> [questions already asked]
        "feedback_history": [],     # list of {date, topic, score, notes}
        "sessions": [],             # list of session metadata
        "total_sessions": 0,
        "last_session": None,
    }


def save_memory(memory: dict) -> None:
    """Persist memory to disk."""
    _ensure_dir()
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


def get_memory_summary(memory: dict) -> str:
    """Return a human-readable string summary for agent consumption."""
    if not memory["topics_covered"]:
        return "No prior preparation sessions found. This is the user's first session."

    lines = [
        f"Total sessions completed: {memory['total_sessions']}",
        f"Last session: {memory.get('last_session', 'Unknown')}",
        f"Topics already covered: {', '.join(memory['topics_covered']) or 'None'}",
        f"Known weak areas: {', '.join(memory['weak_areas']) or 'None identified yet'}",
    ]

    if memory["feedback_history"]:
        recent = memory["feedback_history"][-3:]
        lines.append("Recent feedback snippets:")
        for fb in recent:
            lines.append(f"  - [{fb['date']}] {fb['topic']}: Score {fb.get('score', 'N/A')}/10 — {fb.get('notes', '')}")

    return "\n".join(lines)


def update_memory_after_session(
    memory: dict,
    topics: list[str],
    weak_areas: list[str],
    questions_used: dict[str, list[str]],
    feedback: dict[str, Any],
) -> dict:
    """Update memory with session results and persist."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Merge topics
    for t in topics:
        if t not in memory["topics_covered"]:
            memory["topics_covered"].append(t)

    # Merge weak areas
    for w in weak_areas:
        if w not in memory["weak_areas"]:
            memory["weak_areas"].append(w)

    # Remove resolved weak areas
    resolved = feedback.get("resolved_weak_areas", [])
    memory["weak_areas"] = [w for w in memory["weak_areas"] if w not in resolved]

    # Merge questions seen
    for topic, qs in questions_used.items():
        if topic not in memory["questions_seen"]:
            memory["questions_seen"][topic] = []
        for q in qs:
            if q not in memory["questions_seen"][topic]:
                memory["questions_seen"][topic].append(q)

    # Append feedback entry
    memory["feedback_history"].append({
        "date": now,
        "topic": ", ".join(topics),
        "score": feedback.get("overall_score", "N/A"),
        "notes": feedback.get("summary_notes", ""),
    })

    memory["total_sessions"] += 1
    memory["last_session"] = now
    memory["sessions"].append({"date": now, "topics": topics})

    save_memory(memory)
    return memory
