from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.rule import Rule

from src.utils.find_name import agent_name, user_name
from src.utils.exit_check import check_exit

console = Console()

def _call_and_check(llm_fn, messages, user, console) -> tuple[str, bool]:
    response = llm_fn(messages)
    
    should_exit, goodbye = check_exit(response)

    if should_exit:
        with console.status(f"\n[bold yellow]💾 Saving memory...", spinner="bouncingBar"):
            messages.append({
                "role": "user", 
                "content": f"Finalize: summarize session into memory.yaml and update projects.yaml."
            })
            final = llm_fn(messages)

        console.print(Panel(Markdown(final), title="[bold yellow]Final Memory Sync[/bold yellow]", border_style="yellow"))
        console.print(f"\n[bold green]{goodbye}[/bold green]\n")

        return response, True

    return response, False


def run_loop(
    title: str,
    input_prompt: str,
    llm_fn,                          
    verify_always: bool = False,     
    trigger_phrase: str = "VERIFICATION_REQUIRED",
    on_verify=None):

    agent = agent_name().capitalize()
    agentc = agent.upper()
    user = user_name().capitalize()
    messages = []

    console.print("\n")
    console.print(Rule(f"[bold cyan]{agentc} {title}[/bold cyan]", style="cyan"))
    console.print(Panel.fit(
        f"Identity Verified. [bold magenta]{user}[/bold magenta] session active.\n",
        border_style="blue", padding=(1, 2)
    ))

    while True:
        prompt = Prompt.ask(f"\n[bold green]{input_prompt}[/bold green]").strip()

        messages.append({
            "role": "user",
            "content": prompt
        })

        with console.status(f"\n[bold blue]{agent} is thinking...", spinner="dots"):
            response, exiting = _call_and_check(llm_fn, messages, user, console)

        if exiting:
            break

        messages.append({
            "role": "assistant", 
            "content": response
        })

        console.print("\n", Rule(style="dim"))
        console.print(Panel(Markdown(response), title=f"[bold magenta]{agent} Output[/bold magenta]", border_style="magenta", padding=(1, 2)))
        console.print(Rule(style="dim"))

        should_verify = verify_always or trigger_phrase in response

        if should_verify:
            if on_verify:
                on_verify(messages, llm_fn, console)
            
            else:
                is_correct = Prompt.ask(
                    f"\n[bold yellow]Was this verdict correct?[/bold yellow]",
                    choices=["y", "n", "skip"], default="y"
                )

                if is_correct == "n":
                    ground_truth = Prompt.ask("What is the truth?", choices=["human", "ai"])
                    reason = Prompt.ask("Why was I wrong?")

                    messages.append({
                        "role": "user",
                        "content": f"WRONG VERDICT. Truth: {ground_truth}. Reason: {reason}. Update memory."
                    })

                    correction, exiting = _call_and_check(llm_fn, messages, user, console)

                    if exiting:
                        break

                    messages.append({
                        "role": "assistant",
                        "content": correction
                    })
                    
                    console.print(Panel(Markdown(correction), title="System Update", border_style="green"))

                elif is_correct == "y":
                    messages.append({
                        "role": "user",
                        "content": "Verdict confirmed correct. Update validation_benchmarks with PASS."
                    })

    console.print(Rule(f"[bold cyan]{agentc} TERMINATED SESSION — Bye {user}![/bold cyan]", style="cyan"))

