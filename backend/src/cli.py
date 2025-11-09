# User Input Methods Reference:
#
# 1. Rich console.input() - Simple styled input
#    name = console.input("[cyan]What's your name?[/cyan] ")
#
# 2. Rich Prompt class - With validation and defaults
#    from rich.prompt import Prompt, Confirm, IntPrompt
#    name = Prompt.ask("Enter your name", default="Anonymous")
#    confirmed = Confirm.ask("Continue?")
#    choice = IntPrompt.ask("Your answer (1-4)", choices=["1", "2", "3", "4"])
#
# 3. Click prompts - Click-specific prompts
#    name = click.prompt('Enter your name', default='Anonymous')
#    age = click.prompt('Enter age', type=int)
#    if click.confirm('Continue?'):
#        pass
#
# Example: Multiple choice with IntPrompt
#    console.print("\n[bold]Select your answer:[/bold]")
#    for i, answer in enumerate(session.answers, 1):
#        console.print(f"  [{i}] {answer.answer}")
#    choice = IntPrompt.ask("Your answer (1-4)", choices=["1", "2", "3", "4"])
#    selected_answer = session.answers[choice - 1]

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from .agents.agent_analysis import AnalysisAgent
from .api_client import ClaudeClient
from .interview import InterviewOrchestrator
from .models import Answer, SessionStatus
from .report_formatter import format_report
from .session import SessionManager

console = Console()


@click.group()
def cli():
    # TODO: Add docstring describing Drama Detective
    pass


@cli.command()
@click.argument("incident_name")
def investigate(incident_name):
    console.print("hello")
    console.print(
        Panel(
            f"[bold]Starting investigation:[/bold] [cyan]{incident_name}[/cyan]\n"
            "[dim]Preparing interview questions...[/dim]",
            title="🕵️ Drama Detective",
            border_style="magenta",
        )
    )

    # Get interviewee context
    console.print("\n[bold magenta]First, let me get some context...[/bold magenta]\n")

    # Get name
    interviewee_name = Prompt.ask(
        "[cyan]What's your name?[/cyan]",
        default="Anonymous"
    )

    # Get relationship to incident
    console.print(f"\n[cyan]Hi {interviewee_name}, what's your relationship to this incident?[/cyan]")
    console.print("  [bold]A)[/bold] I was directly involved")
    console.print("  [bold]B)[/bold] I witnessed it happen")
    console.print("  [bold]C)[/bold] Someone told me about it")
    console.print("  [bold]D)[/bold] I'm friends with someone involved")
    console.print("  [bold]E)[/bold] Parasocial observer from reality tv")
    console.print(". [bold]F)[/bold] Resident doctor hearing about nurse drama")
    role_choice = Prompt.ask("Your answer", choices=["A", "B", "C", "D", "E", "F"])

    role_map = {
        "A": "participant",
        "B": "witness",
        "C": "secondhand",
        "D": "friend",
        "E": "parasocial observer from reality tv",
        "F": "Resident doctor hearing about nurse drama"
    }
    interviewee_role = role_map[role_choice]

    console.print(f"\n[green]Got it! Let's dive into the details.[/green]\n")

    # Prompt user for summary - use click.edit() for multi-line support
    console.print("[cyan]Describe what happened (editor will open):[/cyan]")
    summary = click.edit(
        "\n# Enter your incident summary below. Save and close to continue.\n# Lines starting with # will be ignored.\n\n"
    )

    # Validate summary is not empty (filter out comment lines)
    if not summary:
        console.print("[red]Error: Summary cannot be empty[/red]")
        return

    # Remove comment lines and extra whitespace
    summary_lines = [
        line
        for line in summary.split("\n")
        if line.strip() and not line.strip().startswith("#")
    ]
    summary = " ".join(summary_lines).strip()

    if not summary:
        console.print("[red]Error: Summary cannot be empty[/red]")
        return
    # Create SessionManager and new session
    session_manager = SessionManager()
    session = session_manager.create_session(
        incident_name,
        interviewee_name,
        interviewee_role,
        confidence_threshold=30
    )

    # Store interviewee context in session
    session.interviewee_name = interviewee_name
    session.interviewee_role = interviewee_role

    # Create InterviewOrchestrator
    orchestrator = InterviewOrchestrator(session)
    first_question = orchestrator.initialize_investigation(summary, image_data_list=[])
    # Print first question
    console.print(f"\n[bold]First question:[/bold] [cyan]{first_question}[/cyan]")
    # Print first question

    # Start interview loop
    is_complete = False

    while True:
        # get the answers from the session.answers
        session_answers = session.answers
        # display the answers for the user to choose from
        console.print("\n[bold]Select your answer:[/bold]")
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, answer in enumerate(session_answers):
            console.print(f"  [bold]{letters[i]})[/bold] {answer.answer}")

        # Add custom answer option
        custom_letter = letters[len(session_answers)]
        console.print(
            f"  [bold]{custom_letter})[/bold] [dim]Other (provide custom answer)[/dim]"
        )

        # Create list of valid letter choices including custom option
        valid_choices = [letters[i] for i in range(len(session_answers) + 1)]

        # Prompt user to select a letter
        choice_letter = Prompt.ask("Your answer", choices=valid_choices)

        # Check if user selected custom answer option
        if choice_letter == custom_letter:
            # Prompt for custom answer
            custom_answer_text = console.input("\n[cyan]Enter your answer: [/cyan]")

            # Validate custom answer is not empty
            if not custom_answer_text:
                console.print("[red]Error: Answer cannot be empty[/red]")
                continue

            # Create Answer object for custom answer with generic reasoning
            selected_answer = Answer(
                answer=custom_answer_text,
                reasoning="User provided custom answer not matching predefined options",
            )
            selected_answer_text = custom_answer_text
        else:
            # Convert letter back to index (A=0, B=1, C=2, etc.)
            choice_idx = letters.index(choice_letter)

            # Get the actual answer string from the selected Answer object
            selected_answer_text = session_answers[choice_idx].answer
            selected_answer: Answer = session_answers[choice_idx]

        console.print(f"\n[green]You selected:[/green] {selected_answer_text}")
        next_question, is_complete = orchestrator.process_answer(selected_answer)
        session_manager.save_session(session)
        if is_complete:
            console.log("\n[bold] Interview has been complete, onto analyzing")
            run_analysis(session.session_id)
            break
        console.print(f"\n[bold]Next Question:[/bold] [cyan]{next_question}[/cyan]")


@cli.command()
def list():
    """List all investigation sessions"""
    # Create SessionManager
    session_manager = SessionManager()

    # Get all sessions
    sessions = session_manager.list_sessions()

    # If empty, print helpful message
    if not sessions:
        console.print("\n[yellow]No sessions found.[/yellow]")
        console.print(
            "[dim]Start a new investigation with:[/dim] [cyan]drama investigate <incident_name>[/cyan]"
        )
        return

    # Create Rich Table with columns
    table = Table(title="🕵️ Drama Detective Sessions", border_style="magenta")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Incident", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Progress", justify="right")
    table.add_column("Created", style="dim")

    # Add row for each session
    for session in sessions:
        # Format session ID (show first 8 chars)
        session_id_short = session.session_id[:8]

        # Color-code status
        status_colors = {"complete": "green", "active": "yellow", "paused": "blue"}
        status_color = status_colors.get(session.status.value, "white")
        status_display = (
            f"[{status_color}]{session.status.value.upper()}[/{status_color}]"
        )

        # Calculate average confidence from goals
        if session.goals:
            avg_confidence = sum(g.confidence for g in session.goals) / len(
                session.goals
            )
            progress = f"{avg_confidence:.0f}%"
        else:
            progress = "0%"

        # Format timestamp (just show date part for readability)
        created_display = (
            session.created_at.split("T")[0]
            if "T" in session.created_at
            else session.created_at[:10]
        )

        table.add_row(
            session_id_short,
            session.incident_name,
            status_display,
            progress,
            created_display,
        )

    # Print table
    console.print("\n")
    console.print(table)
    console.print(f"\n[dim]Total sessions: {len(sessions)}[/dim]")
    console.print(
        "[dim]Resume a session with:[/dim] [cyan]drama resume <session_id>[/cyan]"
    )


def run_analysis(session_id: str):
    """Internal function to run analysis - can be called from code or CLI"""
    console = Console()
    session_manager = SessionManager()
    loaded_session = session_manager.load_session(session_id)
    console.print(
        Panel(
            f"[bold]Beginning Analysis:[/bold] [cyan]{loaded_session.incident_name}[/cyan]\n"
            "[dim]Preparing the papers...[/dim]",
            title="🧐 Drama Detective",
            border_style="magenta",
        )
    )
    # Create AnalysisAgent
    analysis_agent = AnalysisAgent(client=ClaudeClient())
    analysis = analysis_agent.generate_analysis(
        loaded_session.model_dump(), session_id=loaded_session.session_id
    )
    # Prepare session_data dict with model_dump()
    # Generate analysis
    format_report(analysis, loaded_session.incident_name, console)
    # Format and display report using report_formatter


@cli.command()
@click.argument("session_id")
def analyze(session_id):
    """CLI command wrapper for analysis"""
    run_analysis(session_id)


@cli.command()
@click.argument("session_id")
def resume(session_id):
    """Resume an investigation from a previous session"""
    # Load the session
    session_manager = SessionManager()

    try:
        session = session_manager.load_session(session_id)
    except FileNotFoundError:
        console.print(f"[red]Error: Session '{session_id}' not found[/red]")
        console.print(
            "[dim]Use[/dim] [cyan]drama list[/cyan] [dim]to see available sessions[/dim]"
        )
        return

    # Display resume panel with interviewee context
    interviewee_info = ""
    if session.interviewee_name:
        role_display = session.interviewee_role.capitalize() if session.interviewee_role else "Unknown"
        interviewee_info = f"[dim]Interviewing: {session.interviewee_name} ({role_display})[/dim]\n"

    console.print(
        Panel(
            f"[bold]Resuming investigation:[/bold] [cyan]{session.incident_name}[/cyan]\n"
            f"{interviewee_info}"
            f"[dim]Session ID: {session_id[:8]}...[/dim]\n"
            f"[dim]Turn count: {session.turn_count}[/dim]",
            title="🕵️ Drama Detective",
            border_style="magenta",
        )
    )

    # Check if session is already complete
    if session.status == SessionStatus.COMPLETE:
        console.print("\n[yellow]This investigation is already complete.[/yellow]")
        console.print(
            f"[dim]View the analysis with:[/dim] [cyan]drama analyze {session_id}[/cyan]"
        )
        run_analysis(session.session_id)
        return

    # Show current question
    if session.current_question:
        console.print(
            f"\n[bold]Current question:[/bold] [cyan]{session.current_question}[/cyan]"
        )
    else:
        console.print(
            "[red]Error: Session has no current question. Session may be corrupted.[/red]"
        )
        return

    # Create InterviewOrchestrator with loaded session
    orchestrator = InterviewOrchestrator(session)

    # Start interview loop (same as investigate command)
    while True:
        # Get the answers from the session.answers
        session_answers = session.answers

        # Display the answers for the user to choose from
        console.print("\n[bold]Select your answer:[/bold]")
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, answer in enumerate(session_answers):
            console.print(f"  [bold]{letters[i]})[/bold] {answer.answer}")

        # Add custom answer option
        custom_letter = letters[len(session_answers)]
        console.print(
            f"  [bold]{custom_letter})[/bold] [dim]Other (provide custom answer)[/dim]"
        )

        # Create list of valid letter choices including custom option
        valid_choices = [letters[i] for i in range(len(session_answers) + 1)]

        # Prompt user to select a letter
        choice_letter = Prompt.ask("Your answer", choices=valid_choices)

        # Check if user selected custom answer option
        if choice_letter == custom_letter:
            # Prompt for custom answer
            custom_answer_text = console.input("\n[cyan]Enter your answer: [/cyan]")

            # Validate custom answer is not empty
            if not custom_answer_text:
                console.print("[red]Error: Answer cannot be empty[/red]")
                continue

            # Create Answer object for custom answer with generic reasoning
            selected_answer = Answer(
                answer=custom_answer_text,
                reasoning="User provided custom answer not matching predefined options",
            )
            selected_answer_text = custom_answer_text
        else:
            # Convert letter back to index (A=0, B=1, C=2, etc.)
            choice_idx = letters.index(choice_letter)

            # Get the actual answer string from the selected Answer object
            selected_answer_text = session_answers[choice_idx].answer
            selected_answer: Answer = session_answers[choice_idx]

        console.print(f"\n[green]You selected:[/green] {selected_answer_text}")
        next_question, is_complete = orchestrator.process_answer(selected_answer)
        session_manager.save_session(session)

        if is_complete:
            console.print("\n[bold]Interview has been completed, onto analyzing[/bold]")
            run_analysis(session.session_id)
            break

        console.print(f"\n[bold]Next Question:[/bold] [cyan]{next_question}[/cyan]")


if __name__ == "__main__":
    cli()
