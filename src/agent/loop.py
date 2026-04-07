from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.status import Status
from rich.rule import Rule

from src.utils.find_name import agent_name
from src.utils.find_name import user_name
from src.agent.llm import agent 

console = Console()

agent_name = agent_name().capitalize()
agent_namec = agent_name.upper()
user_name = user_name().capitalize()

def run_agent():
    messages = []

    console.print("\n")
    console.print(Rule(f"[bold cyan]{agent_namec} CORE AGENT[/bold cyan]", style="cyan"))
    console.print(Panel.fit(
        f"Identity Verified. [bold magenta]{user_name}[/bold magenta] session active.\n"
        "[dim]Type 'exit' or 'bye' to persist memory and close.[/dim]",
        border_style="blue",
        padding=(1, 2)
    ))

    while True:
        prompt = Prompt.ask(f"\n[bold green]Ask something to {agent_name}[/bold green]").strip()

        if prompt.lower() in ["quit", "exit", "bye", "q", "e", "b"]:
            with console.status(f"[bold yellow]💾 {agent_name} is saving session memory...", spinner="bouncingBar"):
                save_prompt = f"Finalize: You '{agent_name}' must summarize this session into memory.yaml and update projects.yaml."

                messages.append({
                    "role": "user",
                    "content": save_prompt
                })

                final_response = agent(messages)

            console.print(Panel(
                Markdown(final_response), 
                title="[bold yellow]Final Memory Sync[/bold yellow]", 
                border_style="yellow"
            ))
            console.print(f"[bold green]✅ Memory persisted. Goodbye {user_name}![/bold green]\n")
            break

        messages.append({
            "role": "user",
            "content": prompt
        })
        
        with console.status(f"[bold blue]{agent_name} is thinking...", spinner="dots"):
            response_text = agent(messages)

        messages.append({
            "role": "assistant",
            "content": response_text
        })

        console.print("\n", Rule(style="dim"))
        console.print(Panel(
            Markdown(response_text), 
            title=f"[bold magenta]{agent_name} Output[/bold magenta]", 
            border_style="magenta",
            padding=(1, 2)
        ))
        console.print(Rule(style="dim"))

        if "VERIFICATION_REQUIRED" in response_text:
            is_correct = Prompt.ask(
                f"[bold yellow]Agent {agent_name}: Was this verdict correct?",
                choices=["y", "n", "skip"],
                default="y"
            )

            if is_correct == "n":
                ground_truth = Prompt.ask(
                    f"[bold yellow]Agent {agent_name}: What is the truth?",
                    choices=["human", "ai"]
                )
                
                correction_reason = Prompt.ask(
                    f"[bold yellow]Agent {agent_name}: What is the reason my analysis was incorrect?"
                )
                
                final_correction_prompt = (
                    f"CORRECTION BY USER:\n"
                    f"- Verdict was: INCORRECT\n"
                    f"- Ground Truth: {ground_truth}\n"
                    f"- Error Reason: {correction_reason}\n\n"
                    f"Action for agent(you): Update memory.yaml benchmarks and tool_performance logic now."
                )

                messages.append({
                    "role": "user",
                    "content": final_correction_prompt
                })

                with console.status("[bold blue]Updating memory and recalibrating...", spinner="earth"):
                    final_sync_response = agent(messages)
                    
                    messages.append({
                        "role": "assistant",
                        "content": final_sync_response
                    })
                    
                    console.print("[bold green]Memory Synced.[/bold green]")
                    console.print(Panel(Markdown(final_sync_response), title="System Update", border_style="green"))
            
            elif is_correct == "y":
                messages.append({
                    "role": "user",
                    "content": "User confirmed the verdict is correct. Update validation_benchmarks with a PASS."
                })

    console.print(Rule(f"[bold cyan]{agent_namec} TERMINATED SESSION[/bold cyan]", style="cyan"))
    console.print(Rule(f"[bold cyan]Bye {user_name}![/bold cyan]", style="cyan"))

