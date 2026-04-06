from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.status import Status
from rich.rule import Rule

from src.agent.llm import call_llm

console = Console()

def run_agent():
    messages = []

    console.print("\n")
    console.print(Rule("[bold cyan]VRAKSHA CORE AGENT[/bold cyan]", style="cyan"))
    console.print(Panel.fit(
        "Identity Verified. [bold magenta]Cybro[/bold magenta] session active.\n"
        "[dim]Type 'exit' or 'bye' to persist memory and close.[/dim]",
        border_style="blue",
        padding=(1, 2)
    ))

    while True:
        prompt = Prompt.ask("\n[bold green]Ask something[/bold green]").strip()

        if prompt.lower() in ["quit", "exit", "bye", "q", "e", "b"]:
            with console.status("[bold yellow]💾 Saving session memory...", spinner="bouncingBar"):
                save_prompt = "Finalize: Summarize this session into memory.yaml and update projects.yaml."

                messages.append({
                    "role": "user",
                    "content": save_prompt
                })

                final_response = call_llm(messages)

            console.print(Panel(
                Markdown(final_response), 
                title="[bold yellow]Final Memory Sync[/bold yellow]", 
                border_style="yellow"
            ))
            console.print("[bold green]✅ Memory persisted. Goodbye.[/bold green]\n")
            break

        messages.append({
            "role": "user",
            "content": prompt
        })
        
        with console.status("[bold blue]Agent is processing...", spinner="dots"):
            response_text = call_llm(messages)

        messages.append({
            "role": "assistant",
            "content": response_text
        })

        console.print("\n", Rule(style="dim"))
        console.print(Panel(
            Markdown(response_text), 
            title="[bold magenta]Vraksha Output[/bold magenta]", 
            border_style="magenta",
            padding=(1, 2)
        ))
        console.print(Rule(style="dim"))

    console.print(Rule("[bold cyan]TERMINATING SESSION[/bold cyan]", style="cyan"))