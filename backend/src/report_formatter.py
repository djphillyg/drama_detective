from rich.console import Console
from rich.panel import Panel

from .models import AnalysisReport


def format_report(analysis: AnalysisReport, incident_name: str, console: Console):
    """Format and display the analysis report using Rich formatting"""

    # Print header with Panel
    console.print("\n")
    console.print(
        Panel(
            f"[bold cyan]{incident_name}[/bold cyan]\n[dim]Investigation Complete[/dim]",
            title="🕵️ Final Analysis Report",
            border_style="magenta",
        )
    )

    # Print timeline section
    if analysis.timeline:
        console.print("\n[bold]⏰ Timeline of Events[/bold]")
        console.print("─" * 50)
        for event in analysis.timeline:
            console.print(f"  [cyan]{event.time}[/cyan] - {event.event}")

    # Print key facts section
    if analysis.key_facts:
        console.print("\n[bold]📋 Key Facts Established[/bold]")
        console.print("─" * 50)
        for fact in analysis.key_facts:
            console.print(f"  • {fact}")

    # Print gaps section (if any)
    if analysis.gaps:
        console.print("\n[bold]❓ Unanswered Questions[/bold]")
        console.print("─" * 50)
        for gap in analysis.gaps:
            console.print(f"  • [yellow]{gap}[/yellow]")

    # Print verdict section
    verdict = analysis.verdict
    console.print("\n[bold]⚖️  The Verdict[/bold]")
    console.print("─" * 50)

    # Primary responsibility with percentage
    console.print(
        f"  [bold]Primary Responsibility:[/bold] [red]{verdict.primary_responsibility}[/red] ([red]{verdict.percentage}%[/red])"
    )

    # Reasoning
    if verdict.reasoning:
        console.print(f"  [bold]Reasoning:[/bold] {verdict.reasoning}")

    # Contributing factors
    if verdict.contributing_factors:
        console.print(f"  [bold]Contributing Factors:[/bold] {verdict.contributing_factors}")

    # Print drama rating
    console.print("\n[bold]🔥 Drama Rating[/bold]")
    console.print("─" * 50)
    console.print(f"  [bold]{verdict.drama_rating}/10[/bold]")

    # Visual bar with fire emojis (1-10 scale)
    fire_count = verdict.drama_rating
    fire_bar = "🔥" * fire_count + "⬜" * (10 - fire_count)
    console.print(f"  {fire_bar}")

    # Explanation
    if verdict.drama_rating_explanation:
        console.print(f"  {verdict.drama_rating_explanation}")

    console.print("\n")
