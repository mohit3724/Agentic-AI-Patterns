"""
coach.py
========
Main orchestrator for the Interview Preparation Coach.
Implements the PASSIVE GOAL CREATOR pattern end-to-end.

PATTERN FLOW:
  ┌──────────────────────────────────────────────────────────────┐
  │              PASSIVE GOAL CREATOR PATTERN                     │
  │                                                              │
  │  User Dialogue ──► Goal Interpreter ──► Refined Plan         │
  │       │                  │                   │               │
  │  (natural text)    (checks memory)    (structured sub-goals) │
  │                          │                   │               │
  │                          ▼                   ▼               │
  │                    Memory Store    ──► Downstream Agents      │
  │                    (JSON file)         [Weak Analyzer         │
  │                                         Question Generator    │
  │                                         Mock Interviewer      │
  │                                         Feedback Coach]       │
  └──────────────────────────────────────────────────────────────┘
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from crewai import Crew, Process
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.rule import Rule
from rich.text import Text

from memory_manager import (
    get_memory_summary,
    load_memory,
    update_memory_after_session,
)
from tasks import create_all_tasks

# ── Setup ────────────────────────────────────────────────────────────────────
load_dotenv()
console = Console()

SESSION_LOG_DIR = Path(os.getenv("SESSION_LOG_DIR", "./data/sessions/"))
SESSION_LOG_DIR.mkdir(parents=True, exist_ok=True)


# ── Display Helpers ──────────────────────────────────────────────────────────

def print_banner():
    console.print()
    console.print(Panel.fit(
        Text.from_markup(
            "[bold cyan]🎯 Interview Preparation Coach[/bold cyan]\n"
            "[dim]Powered by: Passive Goal Creator Pattern + CrewAI + Gemini[/dim]\n"
        ),
        border_style="cyan",
        padding=(1, 4),
    ))
    console.print()


def print_section(title: str, style: str = "bold blue"):
    console.print()
    console.print(Rule(title, style=style))
    console.print()


def print_pattern_explanation():
    """Show how the Passive Goal Creator pattern is being applied."""
    console.print(Panel(
        Text.from_markup(
            "[bold yellow]📐 Passive Goal Creator Pattern — Active[/bold yellow]\n\n"
            "[white]Step 1:[/white] [green]User provides natural language goal (you drive the intent)[/green]\n"
            "[white]Step 2:[/white] [green]Goal Interpreter Agent parses intent + checks memory[/green]\n"
            "[white]Step 3:[/white] [green]Refined sub-goals sent to downstream agents[/green]\n"
            "[white]Step 4:[/white] [green]Agents execute: Analyze → Generate → Mock → Feedback[/green]\n"
            "[white]Step 5:[/white] [green]Memory updated for next session continuity[/green]"
        ),
        border_style="yellow",
        padding=(1, 2),
    ))
    console.print()


# ── Parse Memory Update from Agent Output ───────────────────────────────────

def extract_memory_update(feedback_output: str) -> dict:
    """Extract JSON memory update payload from feedback agent output."""
    try:
        # Look for JSON block in output
        json_match = re.search(
            r'```json\s*(\{.*?"memory_update".*?\})\s*```',
            feedback_output,
            re.DOTALL,
        )
        if json_match:
            parsed = json.loads(json_match.group(1))
            return parsed.get("memory_update", {})

        # Fallback: try to find any JSON with memory_update key
        json_match2 = re.search(
            r'"memory_update"\s*:\s*(\{[^}]+\})',
            feedback_output,
            re.DOTALL,
        )
        if json_match2:
            return json.loads(json_match2.group(1))

    except (json.JSONDecodeError, AttributeError):
        pass

    # Last resort: return minimal structure
    return {
        "topics_to_add": [],
        "new_weak_areas": [],
        "resolved_weak_areas": [],
        "questions_used": {},
        "overall_score": "N/A",
        "summary_notes": "Session completed. Manual memory update recommended.",
    }


# ── Save Session Log ─────────────────────────────────────────────────────────

def save_session_log(
    user_goal: str,
    crew_result: str,
    memory_update: dict,
) -> str:
    """Save full session output to a dated log file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = SESSION_LOG_DIR / f"session_{timestamp}.md"

    content = f"""# Interview Prep Session — {timestamp}

## User Goal
{user_goal}

## Session Output
{crew_result}

## Memory Update Applied
```json
{json.dumps(memory_update, indent=2)}
```
"""
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(content)

    return str(log_file)


# ── Main Orchestrator ─────────────────────────────────────────────────────────

def run_interview_coach(user_goal: str) -> str:
    """
    Main entry point for the Passive Goal Creator-based interview coach.

    Args:
        user_goal: Raw user text, e.g., "Prepare me for a data engineer interview on BigQuery and Airflow"

    Returns:
        Full crew output as a string
    """
    print_banner()
    print_pattern_explanation()

    # ── STEP 1: Load Memory (Passive Goal Creator — Memory Check) ────────────
    print_section("Step 1 — Loading Memory Context", "bold magenta")
    memory = load_memory()
    memory_summary = get_memory_summary(memory)
    questions_already_seen = memory.get("questions_seen", {})

    console.print(Panel(
        memory_summary,
        title="[bold]📚 Memory Context[/bold]",
        border_style="magenta",
        padding=(1, 2),
    ))

    # ── STEP 2: Display User Goal ────────────────────────────────────────────
    print_section("Step 2 — User Goal (Passive Input)", "bold green")
    console.print(Panel(
        f'[bold white]"{user_goal}"[/bold white]',
        title="[bold]💬 User's Natural Language Goal[/bold]",
        border_style="green",
        padding=(1, 2),
    ))
    console.print(
        "[dim]↑ This is the 'passive goal' — the user drives the intent through dialogue.[/dim]\n"
        "[dim]  The Goal Interpreter Agent will parse, contextualize, and plan from this.[/dim]"
    )

    # ── STEP 3: Create Tasks & Crew ──────────────────────────────────────────
    print_section("Step 3 — Assembling Agent Crew", "bold cyan")

    tasks, agents = create_all_tasks(
        user_goal=user_goal,
        memory_summary=memory_summary,
        questions_already_seen=questions_already_seen,
    )

    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,  # Sequential: each agent builds on the previous
        verbose=True,
        memory=False,       # We manage memory ourselves via memory_manager.py
        embedder=None,      # Disabled — using our own JSON memory
    )

    console.print("[bold cyan]Crew assembled with 5 specialized agents:[/bold cyan]")
    for name, agent in agents.items():
        console.print(f"  • [green]{agent.role}[/green]")

    # ── STEP 4: Execute Pipeline ─────────────────────────────────────────────
    print_section("Step 4 — Running Preparation Pipeline", "bold yellow")
    console.print("[yellow]Executing 5-stage pipeline... (this may take 2-5 minutes)[/yellow]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task(
            description="[cyan]Running CrewAI pipeline (Goal Interpretation → Weak Areas → Questions → Mock Q&A → Feedback)...",
            total=None,
        )
        result = crew.kickoff()

    # ── STEP 5: Parse & Display Results ─────────────────────────────────────
    print_section("Step 5 — Preparation Session Complete", "bold green")

    result_str = str(result)

    console.print(Markdown(result_str))

    # ── STEP 6: Update Memory ─────────────────────────────────────────────────
    print_section("Step 6 — Updating Memory Store", "bold magenta")

    memory_update = extract_memory_update(result_str)

    topics_covered = memory_update.get("topics_to_add", [])
    weak_areas = memory_update.get("new_weak_areas", [])
    questions_used = memory_update.get("questions_used", {})
    feedback = {
        "resolved_weak_areas": memory_update.get("resolved_weak_areas", []),
        "overall_score": memory_update.get("overall_score", "N/A"),
        "summary_notes": memory_update.get("summary_notes", ""),
    }

    # Fallback topic extraction if memory update parsing failed
    if not topics_covered:
        for keyword in ["bigquery", "airflow", "apache airflow", "big query"]:
            if keyword in user_goal.lower():
                topics_covered.append(keyword.title().replace("Apache ", "").replace("Big Query", "BigQuery"))

    updated_memory = update_memory_after_session(
        memory=memory,
        topics=topics_covered or ["BigQuery", "Airflow"],
        weak_areas=weak_areas,
        questions_used=questions_used,
        feedback=feedback,
    )

    console.print(Panel(
        f"[green]✅ Memory updated successfully![/green]\n\n"
        f"Topics added: {topics_covered}\n"
        f"Weak areas logged: {weak_areas}\n"
        f"Total sessions now: {updated_memory['total_sessions']}\n"
        f"Memory file: {os.getenv('MEMORY_FILE', './data/memory_store.json')}",
        title="[bold]💾 Memory Update[/bold]",
        border_style="green",
        padding=(1, 2),
    ))

    # ── STEP 7: Save Session Log ──────────────────────────────────────────────
    log_path = save_session_log(
        user_goal=user_goal,
        crew_result=result_str,
        memory_update=memory_update,
    )
    console.print(f"\n[dim]📄 Full session saved to: {log_path}[/dim]")

    return result_str


# ── CLI Entry Point ───────────────────────────────────────────────────────────

def main():
    """Interactive CLI for the Interview Preparation Coach."""
    print_banner()

    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        console.print(Panel(
            "[bold red]❌ GEMINI_API_KEY not set![/bold red]\n\n"
            "1. Get your free key at: [link]https://aistudio.google.com/app/apikey[/link]\n"
            "2. Copy [cyan].env.example[/cyan] to [cyan].env[/cyan]\n"
            "3. Set [cyan]GEMINI_API_KEY=your_key_here[/cyan] in the .env file\n"
            "4. Run again",
            border_style="red",
            title="Setup Required",
            padding=(1, 2),
        ))
        sys.exit(1)

    console.print("[bold cyan]Interview Preparation Coach[/bold cyan]")
    console.print("[dim]Powered by Passive Goal Creator Pattern | CrewAI | Gemini Free Tier[/dim]\n")

    # Get user goal (the passive input)
    console.print("[bold green]Tell me your interview preparation goal:[/bold green]")
    console.print("[dim]Example: 'Prepare me for a data engineer interview on BigQuery and Airflow'[/dim]")
    console.print("[dim]Example: 'I have a senior DE interview at Spotify next week, focus on Airflow'[/dim]")
    console.print()

    if len(sys.argv) > 1:
        # Accept goal as command-line argument for non-interactive use
        user_goal = " ".join(sys.argv[1:])
        console.print(f"[dim]Using goal from args: {user_goal}[/dim]")
    else:
        user_goal = console.input("[bold yellow]Your goal > [/bold yellow]").strip()

    if not user_goal:
        user_goal = "Prepare me for a data engineer interview on BigQuery and Airflow"
        console.print(f"[dim]Using default goal: {user_goal}[/dim]")

    # Run the coach
    run_interview_coach(user_goal)

    console.print()
    console.print(Panel(
        "[bold green]🎉 Preparation session complete![/bold green]\n\n"
        "Your memory has been updated. Next session will build on today's work.\n"
        "Run the coach again to continue your preparation journey.",
        border_style="green",
        padding=(1, 2),
    ))


if __name__ == "__main__":
    main()
