"""
pipeline.py
Orchestrates the full Proactive Goal Creator pipeline.

Flow:
  User says "Plan this trip"
       ↓
  [STEP 1] ProactiveGoalCreatorAgent
           Calls all context tools, infers structured goal
       ↓
  [STEP 2] GuardrailAgent
           Validates goal — blocks on hard failures, warns on soft issues
       ↓
  [STEP 3] TravelPlannerAgent
           Generates multi-path itinerary from validated goal
       ↓
  [STEP 4] ReflectionAgent
           Reviews itinerary vs goal, approves or flags issues
       ↓
  Final formatted output to console
"""

import json
import re
import sys
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich import print as rprint

from agents import (
    build_goal_creator_agent,
    build_guardrail_agent,
    build_planner_agent,
    build_reflection_agent,
)
from models import InferredGoal, GuardrailResult, TravelItinerary, ReflectionResult

console = Console()


def _extract_json(text: str) -> str:
    """
    Robustly extracts JSON from an LLM response that may
    contain markdown fences, preamble text, or trailing content.
    """
    # Strip markdown code fences
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```", "", text)
    # Find the outermost JSON object
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON object found in LLM response:\n{text}")
    return text[start:end]


def _parse_json_safe(raw: str, label: str) -> dict:
    try:
        cleaned = _extract_json(raw)
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError) as e:
        console.print(f"[red]JSON parse error in {label}: {e}[/red]")
        console.print(f"[dim]Raw response:\n{raw}[/dim]")
        sys.exit(1)


def _agent_run(agent, prompt: str) -> str:
    """Runs an Agno agent and returns the response content as a string."""
    response = agent.run(prompt)
    # Agno returns a RunResponse; extract the text content
    if hasattr(response, "content"):
        return str(response.content)
    return str(response)


def run_pipeline(user_message: str = "Plan this trip") -> None:

    console.rule("[bold cyan]Smart Travel Planner — Proactive Goal Creator Pattern[/bold cyan]")
    console.print(f"\n[bold yellow]User request:[/bold yellow] \"{user_message}\"\n")

    # ── STEP 1 : Proactive Goal Creator ─────────────────────────────────────
    console.rule("[blue]STEP 1 — Proactive Goal Creator Agent[/blue]")
    console.print(
        "[dim]Pattern role: Sends requirements to context detectors (tools), "
        "captures multimodal context, infers structured goal from underspecified prompt.[/dim]\n"
    )

    goal_agent = build_goal_creator_agent()
    goal_raw   = _agent_run(goal_agent, user_message)

    goal_dict  = _parse_json_safe(goal_raw, "InferredGoal")
    goal       = InferredGoal(**goal_dict)

    console.print(Panel(
        json.dumps(goal.model_dump(), indent=2),
        title="[green]Inferred Goal Object[/green]",
        border_style="green",
    ))

    # Show confidence scores
    console.print("\n[bold]Confidence Scores:[/bold]")
    for field, score in goal.confidence.model_dump().items():
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        console.print(f"  {field:<20} {bar} {score:.0%}")

    if goal.missing_fields:
        console.print(f"\n[yellow]Missing fields:[/yellow] {', '.join(goal.missing_fields)}")
    if goal.assumptions:
        console.print("\n[yellow]Assumptions made:[/yellow]")
        for a in goal.assumptions:
            console.print(f"  • {a}")

    # ── STEP 2 : Guardrail Agent ─────────────────────────────────────────────
    console.rule("[blue]STEP 2 — Guardrail Agent[/blue]")
    console.print(
        "[dim]Pattern role: Multimodal Guardrails — validates inferred goal "
        "for safety, feasibility, visa alerts, and consent before planning begins.[/dim]\n"
    )

    guard_agent = build_guardrail_agent()
    guard_prompt = f"Validate this InferredGoal:\n{json.dumps(goal.model_dump(), indent=2)}"
    guard_raw    = _agent_run(guard_agent, guard_prompt)

    guard_dict   = _parse_json_safe(guard_raw, "GuardrailResult")
    guardrail    = GuardrailResult(**guard_dict)

    status_icon = "✅ PASSED" if guardrail.passed else "🚫 BLOCKED"
    console.print(Panel(
        json.dumps(guardrail.model_dump(), indent=2),
        title=f"[{'green' if guardrail.passed else 'red'}]Guardrail Result — {status_icon}[/{'green' if guardrail.passed else 'red'}]",
        border_style="green" if guardrail.passed else "red",
    ))

    if not guardrail.passed:
        console.print(
            f"\n[red bold]Pipeline halted by Guardrail.[/red bold]\n"
            f"Issues: {guardrail.issues}"
        )
        return

    if guardrail.warnings:
        console.print("\n[yellow]⚠ Guardrail Warnings:[/yellow]")
        for w in guardrail.warnings:
            console.print(f"  • {w}")

    # ── STEP 3 : Travel Planner Agent ────────────────────────────────────────
    console.rule("[blue]STEP 3 — Travel Planner Agent (Multi-Path Plan Generator)[/blue]")
    console.print(
        "[dim]Pattern role: Multi-Path Plan Generator — creates 3 flight options, "
        "3 hotel options, day plans, and a visa checklist from the validated InferredGoal.[/dim]\n"
    )

    planner_agent   = build_planner_agent()
    planner_prompt  = (
        f"Generate a complete travel itinerary for this InferredGoal:\n"
        f"{json.dumps(goal.model_dump(), indent=2)}"
    )
    planner_raw = _agent_run(planner_agent, planner_prompt)

    itinerary_dict = _parse_json_safe(planner_raw, "TravelItinerary")
    itinerary      = TravelItinerary(**itinerary_dict)

    # Print itinerary summary
    console.print(Panel(
        f"[bold]{itinerary.goal_summary}[/bold]",
        title="[cyan]Trip Summary[/cyan]",
        border_style="cyan",
    ))

    console.print("\n[bold cyan]✈  Flight Options:[/bold cyan]")
    for f in itinerary.flight_options:
        marker = "★ RECOMMENDED" if f.option_label == itinerary.recommended_flight else ""
        console.print(
            f"  [{f.option_label}] {f.route} via {f.airline} | "
            f"{f.stops} stop(s) | {f.estimated_cost_inr} {marker}"
        )

    console.print("\n[bold cyan]🏨  Hotel Options:[/bold cyan]")
    for h in itinerary.hotel_options:
        marker = "★ RECOMMENDED" if h.option_label == itinerary.recommended_hotel else ""
        console.print(
            f"  [{h.option_label}] {h.hotel_name} ({h.tier}) | "
            f"{h.distance_to_venue} from venue | "
            f"{h.estimated_cost_per_night_inr}/night × {h.total_nights} nights "
            f"{'+ Breakfast' if h.includes_breakfast else ''} {marker}"
        )

    console.print("\n[bold cyan]📅  Day-by-Day Plan:[/bold cyan]")
    for day in itinerary.day_plans:
        console.print(f"\n  [bold]{day.date}[/bold]")
        console.print(f"    Morning   : {day.morning}")
        console.print(f"    Afternoon : {day.afternoon}")
        console.print(f"    Evening   : {day.evening}")
        if day.transport_note:
            console.print(f"    Transport : {day.transport_note}")

    if itinerary.visa_checklist and itinerary.visa_checklist.required:
        vc = itinerary.visa_checklist
        console.print(Panel(
            f"Type                : {vc.type}\n"
            f"Processing          : ~{vc.estimated_processing_days} working days\n"
            f"Documents needed    : {', '.join(vc.documents_needed)}\n"
            f"Apply at            : {vc.apply_url}",
            title="[red]⚠  Visa Required[/red]",
            border_style="red",
        ))

    console.print(f"\n[bold green]💰 Total Estimated Cost:[/bold green] {itinerary.total_estimated_cost_inr}")

    console.print("\n[bold]🎒 Packing Tips:[/bold]")
    for tip in itinerary.packing_tips:
        console.print(f"  • {tip}")

    # ── STEP 4 : Reflection Agent ─────────────────────────────────────────────
    console.rule("[blue]STEP 4 — Reflection Agent (Self-Reflection)[/blue]")
    console.print(
        "[dim]Pattern role: Self-Reflection — reviews itinerary against goal "
        "for coherence, budget alignment, date consistency, and approves or flags issues.[/dim]\n"
    )

    reflection_agent  = build_reflection_agent()
    reflection_prompt = (
        f"Review coherence between this inferred_goal and itinerary.\n\n"
        f"inferred_goal:\n{json.dumps(goal.model_dump(), indent=2)}\n\n"
        f"itinerary:\n{json.dumps(itinerary.model_dump(), indent=2)}"
    )
    reflection_raw  = _agent_run(reflection_agent, reflection_prompt)
    reflection_dict = _parse_json_safe(reflection_raw, "ReflectionResult")
    reflection      = ReflectionResult(**reflection_dict)

    approval_label = "[green]✅ APPROVED[/green]" if reflection.approved else "[red]🔄 REVISION REQUESTED[/red]"
    console.print(Panel(
        f"Coherent          : {'Yes' if reflection.coherent else 'No'}\n"
        f"Status            : {('APPROVED' if reflection.approved else 'REVISION REQUESTED')}\n"
        f"Final note        : {reflection.final_note}\n"
        + (f"\nIssues            :\n" + "\n".join(f"  • {i}" for i in reflection.issues_found) if reflection.issues_found else "")
        + (f"\nSuggestions       :\n" + "\n".join(f"  • {s}" for s in reflection.suggestions) if reflection.suggestions else ""),
        title=f"[bold]Reflection Result — {('APPROVED' if reflection.approved else 'REVISION REQUESTED')}[/bold]",
        border_style="green" if reflection.approved else "yellow",
    ))

    # ── Final summary ─────────────────────────────────────────────────────────
    console.rule("[bold cyan]Pipeline Complete[/bold cyan]")
    console.print(f"\n[bold]Destination   :[/bold] {goal.destination}")
    console.print(f"[bold]Travel window :[/bold] {goal.travel_window.departure_date} → {goal.travel_window.return_date}")
    console.print(f"[bold]Departing from:[/bold] {goal.departure_city} via {goal.hub_airport}")
    console.print(f"[bold]Budget band   :[/bold] {goal.budget_band.upper()}")
    console.print(f"[bold]Visa required :[/bold] {'Yes — ' + goal.visa_status if goal.visa_required else 'No'}")
    console.print(f"[bold]Reflection    :[/bold] {'Approved ✅' if reflection.approved else 'Needs revision ⚠'}")
    console.print()
