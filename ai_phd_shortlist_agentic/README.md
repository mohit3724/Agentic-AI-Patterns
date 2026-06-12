# AI PhD Shortlist Builder — Agentic Version (CrewAI + LangSmith)

This repository contains an **agentic implementation** of the PhD Shortlist Builder assignment.
It extends a deterministic retrieval + ranking pipeline with a **multi‑agent CrewAI orchestration
layer** and **LangSmith‑based evaluation hooks**.

The system takes a structured student profile JSON and produces a **ranked shortlist** of
supervisors and PhD programs, with evidence and personalised `why_match` blurbs, while
prioritising:

- Low contamination (no wrong‑person / wrong‑domain / non‑PI entries)
- Hard country adherence (all supervisors in the student’s target countries)
- Clear, machine‑readable JSON output

The underlying retrieval logic uses local JSON catalogues so the project is fully
testable offline; the agentic layer is written to be easily swapped onto real data
sources.

---

## High‑Level Architecture

The system has two layers:

1. **Base Pipeline (Deterministic)** — in `src/shortlist_builder/`
   - Encapsulates pure Python logic for:
     - Loading and normalising student profiles (`profile_ingestion.py`).
     - Retrieving candidate supervisors + programs from a local catalogue (`retrieval.py`).
     - Scoring and tiering candidates (`ranking.py`).
     - Generating deterministic `why_match` blurbs (`llm_utils.py`).
   - Can be run directly without any agent framework.

2. **Agentic Orchestration Layer** — in `src/shortlist_builder/agentic/`
   - Implements a **role‑based, orchestrated multi‑agent system** using CrewAI.
   - Agents collaborate to run the same logical pipeline, but with:
     - **Parallel fan‑out** over retrieval tasks.
     - A **Generator–Critic loop** for refining the final shortlist.
     - Hooks for **LangSmith tracing and evaluation metrics**.

This separation keeps domain logic testable and allows different orchestration
strategies (classic pipeline vs agentic) over the same core functions.

---

## Folder Structure

```text
ai_phd_shortlist_agentic/
├── README.md                # This file — architecture & usage
├── requirements.txt         # Dependencies (CrewAI, LangChain, LangSmith)
├── schema.md                # JSON schemas for input and output
├── sample_input/
│   └── sample_student.json  # Example student profile
├── sample_output/
│   └── (generated shortlists)
├── data/
│   ├── supervisors.json     # Toy supervisor catalogue (acts as stand‑in for real APIs)
│   └── programs.json        # Toy program / advert catalogue with eligibility metadata
└── src/
    └── shortlist_builder/
        ├── __init__.py
        ├── models.py               # Dataclasses for student, supervisor, program, shortlist
        ├── profile_ingestion.py    # Parse & normalise student profile JSON
        ├── retrieval.py            # Deterministic candidate retrieval from local catalogues
        ├── ranking.py              # Scoring and tiering logic
        ├── llm_utils.py            # Deterministic why_match templates
        ├── pipeline.py             # Non‑agentic end‑to‑end pipeline
        └── agentic/
            ├── __init__.py
            ├── tools.py            # Thin wrappers exposing base functions as CrewAI tools
            ├── agents.py           # CrewAI agent definitions (Planner, Retrieval, Validator, etc.)
            ├── crew_runner.py      # Orchestrated multi‑agent flow + LangSmith hooks
            └── cli_agentic.py      # CLI entrypoint for running the agentic pipeline
```

---

## What Each Agent Does

All agents are defined in `agentic/agents.py` and wired together in
`agentic/crew_runner.py`.

### 1. PlannerAgent

- **Pattern:** Orchestrated workflow + plan generation.
- Reads the student profile and produces a **high‑level plan**:
  - Normalises `research_interests` into canonical `areas_of_interest`.
  - Decides which retrieval tasks to run (per area) and for which target countries.
- In practice this is implemented as a CrewAI agent that calls a tool
  `plan_retrieval_tasks(profile)` and returns a list of retrieval task specs.

### 2. RetrievalAgent (fan‑out)

- **Pattern:** Role‑based multi‑agent + parallel fan‑out.
- For each area in the plan, the orchestrator creates a CrewAI Task that invokes
  the `run_retrieval_for_area` tool.
- The tool uses the base `retrieval.get_candidate_supervisors` function, filtered
  by the student’s `target_countries`, and tags candidates with the triggering
  area for later scoring.
- CrewAI runs these tasks **in parallel**, giving a merged candidate set across
  all interests.

### 3. PiValidatorAgent

- **Pattern:** Role‑based validation + reflection.
- Receives raw candidates and removes:
  - Non‑PIs (`is_pi == False` in the catalogue).
  - Obvious topic mismatches between supervisor `areas` and student
    `areas_of_interest`.
- In a production system this agent would:
  - Use LLM reflection to inspect publication titles/abstracts.
  - Handle same‑name collisions via author IDs and institution.
- In this reference implementation, the logic is mostly deterministic but still
  routed through an agent for clarity and extensibility.

### 4. EligibilityAgent

- **Pattern:** Role‑based constraint enforcement.
- Calls tools that attach and filter programs based on the student profile:
  - For each candidate’s institution, look up matching programs.
  - Parse and enforce program `eligibility` (open vs restricted citizenship).
  - Enforce **country adherence** strictly.

### 5. RankingAgent

- **Pattern:** Role‑based scorer.
- Uses `ranking.score_and_tier` to compute diagnostic scores:
  - `topic_similarity`, `recent_activity`, `availability`, and composite `overall`.
- Assigns tiers **reach / target / safety** based on rank percentile.

### 6. ShortlistGeneratorAgent + ShortlistCriticAgent

- **Pattern:** Generator–Critic loop.
- `ShortlistGeneratorAgent`:
  - Uses the scored candidates to construct a shortlist object and populates
    deterministic `why_match` blurbs with `llm_utils.generate_why_match`.
- `ShortlistCriticAgent`:
  - Reviews the shortlist and flags issues (e.g., missing evidence, weak
    topic overlap) and can request simple edits (currently: dropping clearly
    weak matches).
- The loop runs for a small, fixed number of iterations to avoid unbounded
  cost and latency.

---

## LangSmith Integration

The module `agentic/crew_runner.py` integrates with **LangSmith** in two ways:

1. **Tracing**
   - If `LANGCHAIN_API_KEY` is set, the run is traced using LangChain’s
     LangSmith integration.
   - This gives end‑to‑end visibility into all agent calls and tools.

2. **Lightweight Evaluations**
   - After generating a shortlist, the code calls `evaluate_shortlist_with_langsmith`,
     which can:
       - Log the shortlist and profile as an example.
       - Run simple evaluators for country adherence and coverage.
   - The implementation is intentionally minimal but shows exactly where
     you would plug in more advanced evaluators or datasets.

If the environment variables for LangSmith are not configured, these hooks
become no‑ops so the pipeline still runs locally.

---

## Installation

You need Python 3.10+.

```bash
cd ai_phd_shortlist_agentic
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

If you want LangSmith tracing/evals, also export:

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your_langsmith_key
export LANGCHAIN_PROJECT="phd-shortlist-agentic"
```

CrewAI will require an LLM provider key (e.g., OpenAI); set the usual env vars
(`OPENAI_API_KEY`, etc.).

---

## Running the Agentic Pipeline

To run the **agentic** version end‑to‑end on the sample profile:

```bash
python -m shortlist_builder.agentic.cli_agentic \
  --input sample_input/sample_student.json \
  --output sample_output/sample_student_shortlist_agentic.json
```

This will:

1. Load and normalise the student profile.
2. PlannerAgent creates per‑area retrieval tasks.
3. RetrievalAgent runs those tasks in parallel over the local catalogue.
4. PiValidatorAgent filters out non‑PIs and weak topical matches.
5. EligibilityAgent enforces country and program eligibility constraints.
6. RankingAgent scores and tiers candidates.
7. ShortlistGeneratorAgent builds the shortlist + why_match blurbs.
8. ShortlistCriticAgent reviews and optionally prunes weaker entries.
9. LangSmith hooks (optional) log and evaluate the run.

The final machine‑readable shortlist JSON is written to the specified output path.

---

## Running the Classic (Non‑Agentic) Pipeline

For comparison, you can run the deterministic pipeline directly:

```bash
python -m shortlist_builder.pipeline_cli \
  --input sample_input/sample_student.json \
  --output sample_output/sample_student_shortlist_classic.json
```

The classic version executes the same logical steps in one linear function
without agents or LangSmith.

---

## Extending to Real Data Sources

To move from the toy JSON catalogues to real scholarly / grant / advert
sources, you mainly need to:

- Replace the implementations in `retrieval.py` with wrappers around APIs
  such as OpenAlex, Semantic Scholar, and grant databases.
- Extend `PiValidatorAgent` prompts to inspect real paper/grant abstracts.
- Improve `EligibilityAgent` to parse full advert text with an LLM.

The agentic layer does not change; it already assumes tools can be swapped
without altering the orchestration logic.
