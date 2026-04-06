from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.status import Status
from rich.rule import Rule

from src.slop_detector.llm import call_llm

console = Console()

def run_detector():
    messages = [] 

    console.print("\n")
    console.print(Rule("[bold cyan]VRAKSHA SLOP DETECTOR[/bold cyan]", style="cyan"))
    console.print(Panel.fit(
        "Welcome, [bold magenta]Cybro[/bold magenta]. System initialized.\n"
        "[dim]Commands: 'quit', 'exit', 'bye', 'q', 'e', 'b'[/dim]",
        border_style="blue",
        padding=(1, 2)
    ))

    while True:
        prompt = Prompt.ask("\n[bold green]Repo URL or Question[/bold green]")

        if prompt.lower() in ["quit", "exit", "bye", "q", "e", "b"]:
            with console.status("[bold yellow]💾 Finalizing & Saving Session Memory...", spinner="bouncingBar"):
                save_prompt = "Finalize: Summarize this session into memory.yaml and update projects.yaml."
                
                messages.append({
                    "role": "user",
                    "content": save_prompt
                })
                
                final_response = call_llm(messages)

            console.print(Panel(
                Markdown(final_response), 
                title="[bold yellow]Final Summary[/bold yellow]", 
                border_style="yellow"
            ))
            console.print("[bold green]✅ Memory persisted. Goodbye.[/bold green]\n")
            break

        messages.append({
            "role": "user",
            "content": prompt
        })

        with console.status("[bold blue]Forensic analysis in progress...", spinner="dots"):
            response_text = call_llm(messages)

        messages.append({
            "role": "assistant",
            "content": response_text
        })

        console.print("\n", Rule(style="dim"))
        console.print(Panel(
            Markdown(response_text), 
            title="[bold magenta]Agent Verdict[/bold magenta]", 
            border_style="magenta",
            padding=(1, 2)
        ))
        console.print(Rule(style="dim"))

    console.print(Rule("[bold cyan]SESSION CLOSED[/bold cyan]", style="cyan"))

