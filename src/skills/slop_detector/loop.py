from src.utils.base_loop import run_loop
from src.skills.slop_detector.llm import detector_agent

def _slop_verify(messages, llm_fn, console):
    is_correct = Prompt.ask(
        "\n[bold yellow]Was this verdict correct?[/bold yellow]",
        choices=["y", "n", "skip"], default="y"
    )
    if is_correct == "n":
        ground_truth = Prompt.ask("What is the truth?", choices=["human", "ai"])
        reason = Prompt.ask("Why was I wrong?")
        messages.append({"role": "user", "content": f"WRONG VERDICT. Truth: {ground_truth}. Reason: {reason}. Update memory."})
        correction = llm_fn(messages)
        messages.append({"role": "assistant", "content": correction})
        console.print(Panel(Markdown(correction), title="System Update", border_style="green"))
        
    elif is_correct == "y":
        messages.append({"role": "user", "content": "Verdict confirmed correct. Update validation_benchmarks with PASS."})

def run_detector():
    run_loop(
        title="SLOP DETECTOR",
        input_prompt="Repo URL or Question",
        llm_fn=detector_agent,
        verify_always=True,
        on_verify=_slop_verify
    )

    