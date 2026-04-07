from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.status import Status
from rich.rule import Rule

from src.utils.find_name import agent_name
from src.utils.find_name import user_name
from src.slop_detector.llm import detector_agent

console = Console()

agent_name = agent_name().capitalize()
agent_namec = agent_name.upper()
user_name = user_name().capitalize()

def run_detector():
    messages = [] 

    console.print("\n")
    console.print(Rule(f"[bold cyan]{agent_namec} SLOP DETECTOR AGENT[/bold cyan]", style="cyan"))
    console.print(Panel.fit(
        f"Welcome, [bold magenta]{user_name}[/bold magenta]. System initialized.\n"
        "[dim]Commands: 'quit', 'exit', 'bye', 'q', 'e', 'b'[/dim]",
        border_style="blue",
        padding=(1, 2)
    ))

    while True:
        prompt = Prompt.ask("\n[bold green]Repo URL or Question[/bold green]")

        if prompt.lower() in ["quit", "exit", "bye", "q", "e", "b"]:
            if len(messages) == 0:
                console.print(Rule(f"[bold cyan]{agent_name}: Bye {user_name} ![/bold cyan]", style="cyan"))
                break

        if prompt.lower() in ["quit", "exit", "bye", "q", "e", "b"]:
            with console.status(f"[bold yellow]💾 {agent_name} is saving session memory...", spinner="bouncingBar"):
                save_prompt = f"Finalize: You '{agent_name}' must summarize this session into memory.yaml and update projects.yaml."
                
                messages.append({
                    "role": "user",
                    "content": save_prompt
                })
                
                final_response = detector_agent(messages)

            console.print(Panel(
                Markdown(final_response), 
                title="[bold yellow]Final Summary[/bold yellow]", 
                border_style="yellow"
            ))
            console.print(f"[bold green]✅ Memory persisted. Goodbye {user_name}![/bold green]\n")
            break

        messages.append({
            "role": "user",
            "content": prompt
        })

        with console.status(f"[bold blue]{agent_name} is analysing...", spinner="dots"):
            response_text = detector_agent(messages)

        messages.append({
            "role": "assistant",
            "content": response_text
        })

        console.print("\n", Rule(style="dim"))
        console.print(Panel(
            Markdown(response_text), 
            title=f"[bold magenta]{agent_name} Agent Verdict[/bold magenta]", 
            border_style="magenta",
            padding=(1, 2)
        ))
        console.print(Rule(style="dim"))

        # After the agent gives its verdict...
        is_correct = Prompt.ask(
            f"\n[bold yellow]{agent_name}: Was this verdict correct?[/bold yellow]", 
            choices=["y", "n", "skip"], 
            default="y"
        )

        if is_correct == "n":
            ground_truth = Prompt.ask(f"{agent_name}: What is the actual truth?", choices=["human", "ai"])
            correction_reason = Prompt.ask(f"{agent_name}: Why was I wrong? (e.g., 'Too much weight on README')")
            
            # Send this back to the agent so it can update memory.yaml
            messages.append({
                "role": "user", 
                "content": f"WRONG VERDICT. Actual truth: {ground_truth}. Reason for failure: {correction_reason}. Update your validation_benchmarks and tool_performance notes."
            })
            # Run one more quick call to let it 'repent' and update the files
            response = detector_agent(messages)

            console.print(Panel(
                Markdown(response), 
                title=f"[bold magenta]{agent_name} Agent Verdict[/bold magenta]", 
                border_style="magenta",
                padding=(1, 2)
            ))

    console.print(Rule(f"[bold cyan]{agent_namec} IS TERMINATING SESSION\nBye {user_name}[/bold cyan]", style="cyan"))

