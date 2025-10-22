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
from rich.table import Table
from rich.prompt import Prompt
from src.session import SessionManager
from src.interview import InterviewOrchestrator
from src.models import Answer

console = Console()


@click.group()
def cli():
    # TODO: Add docstring describing Drama Detective
    pass


@cli.command()
@click.argument('incident_name')
def investigate(incident_name):
    console.print(Panel(
        f"[bold]Starting investigation:[/bold] [cyan]{incident_name}[/cyan]\n"
        "[dim]Preparing interview questions...[/dim]",
        title="🕵️ Drama Detective",
        border_style="magenta"
    ))
    # Prompt user for summary using console.input()
    summary = console.input("\n[cyan]Describe what happened: [/cyan] ")
    # Validate summary is not empty
    if not summary:
        console.print("[red]Error: Summary cannot be empty[/red]")
        return
    # Create SessionManager and new session
    session_manager = SessionManager()
    session = session_manager.create_session(incident_name)
    # Create InterviewOrchestrator
    orchestrator = InterviewOrchestrator(session)
    first_question = orchestrator.initialize_investigation(summary)
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
        console.print(f"  [bold]{custom_letter})[/bold] [dim]Other (provide custom answer)[/dim]")

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
                reasoning="User provided custom answer not matching predefined options"
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
            analyze(session.session_id)
            break
        console.print(f"\n[bold]Next Question:[/bold] [cyan]{next_question}[/cyan]")
    
          
          
        
        # TODO: Start interview loop:
        # - Get user answer via console.input()
        # - Handle quit/exit/stop commands (save as paused)
        # - Validate answer not empty
        # - Process answer through orchestrator
        # - Save session after each turn
        # - If complete, print completion message with analyze command
        # - Print next question and continue loop
      

@cli.command()
def list():
    # TODO: Print placeholder message "coming soon"
    pass


@cli.command()
@click.argument('session_id')
def analyze(session_id):
    # TODO: Print placeholder message with session_id
    
    pass


@cli.command()
@click.argument('session_id')
def resume(session_id):
    # TODO: Print placeholder message with session_id
    pass


if __name__ == '__main__':
    cli()