"""
tasks.py
========
Defines all CrewAI Tasks for the Interview Preparation Coach pipeline.

PASSIVE GOAL CREATOR PIPELINE:
  User Text Goal
      │
      ▼
  Task 1: Interpret Goal + Check Memory  ← PASSIVE GOAL CREATOR STEP
      │ (Refined Plan with sub-goals)
      ▼
  Task 2: Identify Weak Areas
      │ (Weak areas report)
      ▼
  Task 3: Generate Interview Questions
      │ (Categorized question bank)
      ▼
  Task 4: Run Mock Q&A Session
      │ (Mock interview transcript)
      ▼
  Task 5: Generate Feedback + Study Plan
      │ (Structured feedback + memory update payload)
"""

from crewai import Task
from agents import (
    create_goal_interpreter_agent,
    create_weak_area_analyzer_agent,
    create_question_generator_agent,
    create_mock_interviewer_agent,
    create_feedback_coach_agent,
)


def create_all_tasks(
    user_goal: str,
    memory_summary: str,
    questions_already_seen: dict,
) -> tuple[list[Task], dict]:
    """
    Creates the full task pipeline and returns (tasks, agents_dict).

    Args:
        user_goal: Raw user input text (the "passive goal")
        memory_summary: Human-readable string from memory_manager.get_memory_summary()
        questions_already_seen: Dict of topic -> [question strings] from memory
    """
    # ── Instantiate agents ──────────────────────────────────────────────────
    goal_interpreter   = create_goal_interpreter_agent()
    weak_analyzer      = create_weak_area_analyzer_agent()
    question_generator = create_question_generator_agent()
    mock_interviewer   = create_mock_interviewer_agent()
    feedback_coach     = create_feedback_coach_agent()

    agents = {
        "goal_interpreter":   goal_interpreter,
        "weak_analyzer":      weak_analyzer,
        "question_generator": question_generator,
        "mock_interviewer":   mock_interviewer,
        "feedback_coach":     feedback_coach,
    }

    # Format questions already seen for the prompt
    seen_q_str = "\n".join(
        f"  {topic}: {qs[:3]}" for topic, qs in questions_already_seen.items()
    ) or "  None"

    # ────────────────────────────────────────────────────────────────────────
    # TASK 1 — PASSIVE GOAL CREATOR: Interpret User Goal + Create Plan
    # ────────────────────────────────────────────────────────────────────────
    task_interpret_goal = Task(
        description=f"""
## USER'S RAW GOAL (from dialogue interface):
"{user_goal}"

## MEMORY CONTEXT (from prior preparation sessions):
{memory_summary}

## YOUR JOB (Passive Goal Creator Pattern):
You are the ENTRY POINT of this system. The user has spoken naturally — your job is to:

1. **Parse Intent**: Extract the core interview preparation request:
   - What topics/technologies are mentioned? (e.g., BigQuery, Airflow)
   - What role/level is implied? (e.g., Data Engineer, Senior, etc.)
   - What type of preparation is needed? (conceptual, coding, system design, all-around?)

2. **Check Memory**: Based on the memory context above:
   - Which of the mentioned topics have been covered before?
   - Are there known weak areas from prior sessions?
   - What's NEW this session vs. what's already been done?

3. **Create Refined Sub-Goals**: Output a STRUCTURED PREPARATION PLAN with these components:
   - **Session Goal**: One-sentence refined objective
   - **Topics to Cover**: List with priority (P1/P2/P3)
   - **Focus Areas**: Specific sub-topics based on memory gaps
   - **Plan Steps**: Ordered list: [Weak Area Analysis → Question Generation → Mock Q&A → Feedback]
   - **Context for Agents**: Brief notes for downstream agents on what to focus on

Output this as a clear, structured plan that downstream agents will use.
""",
        expected_output="""
A structured JSON-like preparation plan containing:
{
  "session_goal": "...",
  "topics": [{"name": "BigQuery", "priority": "P1", "sub_topics": [...]}, ...],
  "prior_coverage": [...],
  "known_weak_areas": [...],
  "focus_recommendation": "...",
  "plan_steps": ["Step 1: ...", "Step 2: ...", ...],
  "agent_context_notes": "..."
}
""",
        agent=goal_interpreter,
    )

    # ────────────────────────────────────────────────────────────────────────
    # TASK 2 — Identify Weak Areas
    # ────────────────────────────────────────────────────────────────────────
    task_identify_weak_areas = Task(
        description=f"""
## CONTEXT:
You have received the structured preparation plan from the Goal Interpreter Agent.

## MEMORY CONTEXT:
{memory_summary}

## YOUR JOB:
Based on the preparation plan and memory context, perform a comprehensive WEAK AREA ANALYSIS:

1. **Topic Breakdown**: For each topic in the plan (BigQuery, Airflow, etc.), list ALL major sub-topics:
   - BigQuery: partitioning, clustering, query optimization, cost management, streaming inserts,
     table schemas, views vs materialized views, BigQuery ML, Data Transfer Service, etc.
   - Airflow: DAG structure, operators (BashOperator, PythonOperator, etc.), XComs, Hooks,
     Sensors, scheduling/cron, backfilling, task dependencies, pools, connections, Variables,
     monitoring, best practices, etc.

2. **Gap Identification**: For each sub-topic, classify as:
   - 🔴 CRITICAL GAP (never covered OR flagged as weak in memory)
   - 🟡 PARTIAL KNOWLEDGE (covered but needs reinforcement)
   - 🟢 STRONG (well-covered in memory — deprioritize)

3. **Priority Matrix**: Rank top 5-7 weak areas to focus on this session.

4. **Complexity Assessment**: Note which topics are commonly asked in senior-level interviews.
""",
        expected_output="""
A detailed weak areas report with:
- Sub-topic classification (Critical/Partial/Strong) for BigQuery and Airflow
- Top 5-7 prioritized weak areas to focus on this session
- Note on which topics are frequently tested at senior-level interviews
- Recommended depth of coverage per weak area
""",
        agent=weak_analyzer,
        context=[task_interpret_goal],
    )

    # ────────────────────────────────────────────────────────────────────────
    # TASK 3 — Generate Interview Questions
    # ────────────────────────────────────────────────────────────────────────
    task_generate_questions = Task(
        description=f"""
## CONTEXT:
You have the preparation plan and weak areas analysis from previous agents.

## QUESTIONS ALREADY SEEN IN PRIOR SESSIONS (DO NOT REPEAT THESE):
{seen_q_str}

## YOUR JOB:
Generate a COMPREHENSIVE QUESTION BANK for this mock interview session.

For each topic (BigQuery + Airflow), generate questions across 4 categories:

### Category A — Conceptual / Theoretical (3-4 questions per topic)
Test foundational understanding. E.g., "What is the difference between partitioning and clustering in BigQuery?"

### Category B — Practical / Scenario-Based (3-4 questions per topic)
Real-world problem-solving. E.g., "Your BigQuery query is scanning too much data and costs are high. How do you optimize?"

### Category C — System Design (2-3 questions per topic)
Architecture decisions. E.g., "Design a data pipeline that ingests 10M events/day into BigQuery with minimal latency."

### Category D — Troubleshooting / Debugging (2 questions per topic)
Diagnosing issues. E.g., "Your Airflow DAG is stuck with tasks in 'queued' state. How do you debug this?"

**CRITICAL**: Do NOT include any questions from the "QUESTIONS ALREADY SEEN" list above.
Focus more questions on the CRITICAL GAP areas identified by the Weak Area Analyzer.
""",
        expected_output="""
A structured question bank with:
- 4 categories (Conceptual, Practical, System Design, Troubleshooting)
- 10-14 questions per topic (BigQuery, Airflow) = 20-28 total questions
- Each question labeled with: Topic | Category | Difficulty (Easy/Medium/Hard)
- Questions ordered by priority (critical gap areas first)
""",
        agent=question_generator,
        context=[task_interpret_goal, task_identify_weak_areas],
    )

    # ────────────────────────────────────────────────────────────────────────
    # TASK 4 — Run Mock Q&A Interview
    # ────────────────────────────────────────────────────────────────────────
    task_mock_interview = Task(
        description=f"""
## CONTEXT:
You have the full question bank from the Question Generator.

## YOUR JOB:
Conduct a MOCK INTERVIEW SESSION. Select the TOP 8-10 most important questions
from the question bank (prioritizing critical gap areas and hard/medium difficulty).

For each selected question, format as a COMPLETE mock interview exchange:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUESTION [N] | Topic: [BigQuery/Airflow] | Category: [...] | Difficulty: [...]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎤 INTERVIEWER: [The question, phrased naturally as an interviewer would ask it]

💡 WHAT A STRONG ANSWER INCLUDES:
   [Key points the candidate must mention to give a complete answer]

✅ MODEL ANSWER:
   [A detailed, ideal answer that demonstrates senior-level understanding.
    Include specific technical details, examples, and best practices.]

⚠️ COMMON MISTAKES:
   [1-2 things candidates typically get wrong or miss]

🔁 LIKELY FOLLOW-UP:
   [One follow-up question the interviewer might ask]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Cover at least 4-5 questions from each topic (BigQuery + Airflow).
This transcript is the core learning material for the candidate.
""",
        expected_output="""
A complete mock interview transcript with:
- 8-10 questions total (4-5 BigQuery, 4-5 Airflow)
- Full formatted exchange for each question (as described above)
- Interviewer phrasing, key answer points, model answer, common mistakes, follow-up
- Questions ordered from most important/critical to nice-to-have
""",
        agent=mock_interviewer,
        context=[task_interpret_goal, task_identify_weak_areas, task_generate_questions],
    )

    # ────────────────────────────────────────────────────────────────────────
    # TASK 5 — Feedback, Scoring & Memory Update
    # ────────────────────────────────────────────────────────────────────────
    task_feedback = Task(
        description=f"""
## CONTEXT:
You have the complete mock interview transcript and all prior agent outputs.

## YOUR JOB:
Provide STRUCTURED FEEDBACK and generate a MEMORY UPDATE PAYLOAD.

### SECTION 1 — SESSION PERFORMANCE REPORT
Score the candidate's readiness (based on question difficulty and coverage):
- BigQuery readiness score: X/10
- Airflow readiness score: X/10
- Overall score: X/10

### SECTION 2 — TOPIC-BY-TOPIC ANALYSIS
For each major sub-topic covered:
- ✅ Strong points (what they likely know well from context)
- ❌ Gaps identified (what the mock Q&A revealed they need to study)
- 📚 Specific resources (official docs links, key concepts to review)

### SECTION 3 — TOP 5 PRIORITY ACTION ITEMS
Numbered list of the most important things to study before the actual interview.
Be SPECIFIC: not "study BigQuery" but "Study BigQuery partitioned table best practices —
specifically how to choose partition columns and when to use PARTITION BY DATE vs INGESTION TIME".

### SECTION 4 — STUDY PLAN (Next 3 days)
Day 1: [Focus area + specific tasks]
Day 2: [Focus area + specific tasks]
Day 3: [Focus area + specific tasks / mock practice]

### SECTION 5 — MEMORY UPDATE PAYLOAD (for system use)
Output this JSON block at the end:
```json
{{
  "memory_update": {{
    "topics_to_add": [...],
    "new_weak_areas": [...],
    "resolved_weak_areas": [...],
    "questions_used": {{"BigQuery": [...], "Airflow": [...]}},
    "overall_score": <number>,
    "summary_notes": "..."
  }}
}}
```
""",
        expected_output="""
A complete feedback report with:
1. Performance scores per topic (BigQuery, Airflow) + overall
2. Topic-by-topic strength/gap analysis with specific resources
3. Top 5 priority action items (specific and actionable)
4. 3-day study plan
5. JSON memory update payload at the end
""",
        agent=feedback_coach,
        context=[
            task_interpret_goal,
            task_identify_weak_areas,
            task_generate_questions,
            task_mock_interview,
        ],
    )

    tasks = [
        task_interpret_goal,
        task_identify_weak_areas,
        task_generate_questions,
        task_mock_interview,
        task_feedback,
    ]

    return tasks, agents
