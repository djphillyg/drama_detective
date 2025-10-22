from rich.console import Console
from rich.panel import Panel

def format_report(analysis: dict, incident_name: str, console: Console):
    """Format and display the analysis report using Rich formatting"""

    # Print header with Panel
    console.print("\n")
    console.print(Panel(
        f"[bold cyan]{incident_name}[/bold cyan]\n[dim]Investigation Complete[/dim]",
        title="🕵️ Final Analysis Report",
        border_style="magenta"
    ))

    # Print timeline section
    if analysis.get("timeline"):
        console.print("\n[bold]⏰ Timeline of Events[/bold]")
        console.print("─" * 50)
        for event in analysis["timeline"]:
            time = event.get("time", "Unknown")
            description = event.get("event", "")
            console.print(f"  [cyan]{time}[/cyan] - {description}")

    # Print key facts section
    if analysis.get("key_facts"):
        console.print("\n[bold]📋 Key Facts Established[/bold]")
        console.print("─" * 50)
        for fact in analysis["key_facts"]:
            console.print(f"  • {fact}")

    # Print gaps section (if any)
    if analysis.get("gaps"):
        console.print("\n[bold]❓ Unanswered Questions[/bold]")
        console.print("─" * 50)
        for gap in analysis["gaps"]:
            console.print(f"  • [yellow]{gap}[/yellow]")

    # Print verdict section
    verdict = analysis.get("verdict", {})
    if verdict:
        console.print("\n[bold]⚖️  The Verdict[/bold]")
        console.print("─" * 50)

        # Primary responsibility with percentage
        primary = verdict.get("primary_responsibility", "Unknown")
        percentage = verdict.get("percentage", 0)
        console.print(f"  [bold]Primary Responsibility:[/bold] [red]{primary}[/red] ([red]{percentage}%[/red])")

        # Reasoning
        reasoning = verdict.get("reasoning", "")
        if reasoning:
            console.print(f"  [bold]Reasoning:[/bold] {reasoning}")

        # Contributing factors
        contributing = verdict.get("contributing_factors", "")
        if contributing:
            console.print(f"  [bold]Contributing Factors:[/bold] {contributing}")

        # Print drama rating
        drama_rating = verdict.get("drama_rating", 0)
        drama_explanation = verdict.get("drama_rating_explanation", "")

        console.print("\n[bold]🔥 Drama Rating[/bold]")
        console.print("─" * 50)
        console.print(f"  [bold]{drama_rating}/10[/bold]")

        # Visual bar with fire emojis (1-10 scale)
        fire_count = drama_rating
        fire_bar = "🔥" * fire_count + "⬜" * (10 - fire_count)
        console.print(f"  {fire_bar}")

        # Explanation
        if drama_explanation:
            console.print(f"  {drama_explanation}")

    console.print("\n")