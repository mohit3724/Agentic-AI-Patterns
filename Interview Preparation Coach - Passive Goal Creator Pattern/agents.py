"""
agents.py
=========
Defines all CrewAI agents for the Interview Preparation Coach.

PASSIVE GOAL CREATOR PATTERN (from IIITH Design Patterns lecture):
--------------------------------------------------------------------
1. User provides goal via natural language dialogue (ambiguous/high-level)
2. Goal Interpreter Agent → parses intent, checks memory, creates refined plan
3. Downstream agents execute the plan steps:
   - Weak Area Analyzer  → identifies knowledge gaps
   - Question Generator  → creates topic-specific Q&A bank
   - Mock Interviewer    → runs interactive Q&A drill
   - Feedback Coach      → gives structured, actionable feedback
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from crewai import Agent, LLM


def get_llm(temperature: float = 0.7) -> LLM:
    model_name = os.getenv("GEMINI_MODEL")
    api_key = os.getenv("GEMINI_API_KEY") 

    if not api_key:
        raise ValueError("Set GEMINI_API_KEY  in .env")

    return LLM(
        model=f"gemini/{model_name}",
        api_key=api_key,
        temperature=temperature
    )

# ─────────────────────────────────────────────────────────
# Agent 1 — Goal Interpreter (PASSIVE GOAL CREATOR CORE)
# ─────────────────────────────────────────────────────────
def create_goal_interpreter_agent() -> Agent:
    """
    THE KEY AGENT in the Passive Goal Creator pattern.
    - Receives raw user text (e.g., "Prepare me for a data engineer interview on BigQuery and Airflow")
    - Checks memory context (previously covered topics, weak areas)
    - Parses intent: extracts topics, experience level, focus areas
    - Generates a REFINED PREPARATION PLAN with concrete sub-goals
    """
    return Agent(
        role="Interview Goal Interpreter & Planner",
        goal=(
            "Parse the user's interview preparation request, check memory for prior sessions, "
            "identify topics to cover, and produce a structured preparation plan with prioritized sub-goals."
        ),
        backstory=(
            "You are an expert interview strategist with 15+ years of experience in technical recruiting "
            "for data engineering roles at top tech companies. You specialize in reading between the lines "
            "of what a candidate says they want and mapping it to what will actually help them succeed. "
            "You operate as the entry point of a Passive Goal Creator pattern — the user drives the goal "
            "through dialogue, and you interpret, contextualize, and structure it into an actionable plan. "
            "You always check memory for previously covered topics to avoid repetition and focus on gaps."
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_llm(temperature=0.3),  # Low temp for structured planning
    )


# ─────────────────────────────────────────────────────────
# Agent 2 — Weak Area Analyzer
# ─────────────────────────────────────────────────────────
def create_weak_area_analyzer_agent() -> Agent:
    """
    Analyzes the identified topics and user memory to determine weak areas.
    Uses known gaps from prior sessions + topic complexity to prioritize focus.
    """
    return Agent(
        role="Technical Weakness Detector & Gap Analyzer",
        goal=(
            "Analyze the topics identified by the planner, cross-reference with memory of prior sessions, "
            "and identify specific weak areas and knowledge gaps the candidate should focus on."
        ),
        backstory=(
            "You are a technical skills assessment expert who has interviewed hundreds of data engineers. "
            "You have deep expertise in BigQuery (partitioning, clustering, query optimization, streaming, "
            "cost management), Apache Airflow (DAGs, operators, XComs, hooks, sensors, scheduling, "
            "backfilling, task dependencies), and data engineering fundamentals. "
            "You can pinpoint exactly which sub-topics trip up candidates at each experience level, "
            "and you use session memory to avoid re-testing areas the user has already mastered."
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_llm(temperature=0.4),
    )


# ─────────────────────────────────────────────────────────
# Agent 3 — Question Generator
# ─────────────────────────────────────────────────────────
def create_question_generator_agent() -> Agent:
    """
    Generates a rich bank of likely interview questions categorized by:
    - Conceptual/Theoretical
    - Practical/Scenario-based
    - System Design
    - Troubleshooting/Debugging
    Avoids questions already seen in memory.
    """
    return Agent(
        role="Senior Interview Question Specialist",
        goal=(
            "Generate a comprehensive, categorized bank of realistic interview questions "
            "for the specified topics, tailored to the weak areas identified. "
            "Ensure questions are fresh (not repeated from memory) and span multiple difficulty levels."
        ),
        backstory=(
            "You have compiled and studied thousands of data engineering interview questions from "
            "FAANG, top startups, and consulting firms. You know exactly what Google, Meta, Spotify, "
            "and unicorn startups ask about BigQuery and Airflow. You generate questions that test "
            "genuine understanding, not surface-level memorization. You categorize questions into "
            "conceptual, hands-on/scenario, system design, and debugging categories. "
            "You check the 'questions already seen' memory to never repeat questions."
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_llm(temperature=0.6),
    )


# ─────────────────────────────────────────────────────────
# Agent 4 — Mock Interviewer
# ─────────────────────────────────────────────────────────
def create_mock_interviewer_agent() -> Agent:
    """
    Simulates a real technical interview.
    - Picks questions from the generated bank
    - Simulates asking questions one by one
    - For each question, also generates a model answer
    - Formats as a realistic mock Q&A transcript
    """
    return Agent(
        role="Expert Technical Mock Interviewer",
        goal=(
            "Conduct a realistic mock interview session by selecting the most important questions "
            "from the question bank, presenting them as an interviewer would, and providing "
            "ideal model answers for each to help the candidate learn."
        ),
        backstory=(
            "You are a seasoned technical interviewer who has conducted 1000+ technical interviews "
            "at tier-1 tech companies. You know how to make interviews feel real — you probe with "
            "follow-up questions, notice when an answer is incomplete, and guide candidates toward "
            "better answers through structured hints. For this training session, you present each "
            "question as the interviewer AND provide a detailed model answer so the candidate can "
            "learn and self-assess. You focus on the weak areas flagged by the analyzer."
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_llm(temperature=0.5),
    )


# ─────────────────────────────────────────────────────────
# Agent 5 — Feedback Coach
# ─────────────────────────────────────────────────────────
def create_feedback_coach_agent() -> Agent:
    """
    Reviews the mock Q&A session and provides:
    - Per-topic performance score (1-10)
    - Specific gaps identified
    - Actionable improvement recommendations
    - Study resources (docs, concepts to review)
    - Updated weak areas list for memory
    """
    return Agent(
        role="Interview Performance Coach & Feedback Specialist",
        goal=(
            "Analyze the mock interview transcript, assess performance per topic, "
            "identify remaining gaps, provide a structured improvement roadmap, "
            "and output a memory update payload (resolved areas, persistent weak areas, overall score)."
        ),
        backstory=(
            "You are a career coach who specializes in helping data engineers crack senior-level interviews. "
            "Your feedback is always specific, actionable, and encouraging — you never just say 'study more'. "
            "You pinpoint exactly which concepts need work, suggest specific documentation to read "
            "(e.g., 'Read the BigQuery partitioned tables documentation and practice PARTITION BY DATE'), "
            "and give honest scores. You also output a structured memory update so the next session "
            "builds on this one rather than repeating the same ground."
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_llm(temperature=0.4),
    )
