from pathlib import Path

from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.text import Text
from rich.theme import Theme
from rich.padding import Padding
from rich.table import Table
from rich import box

from src.utils.find_name import agent_name, user_name
from src.utils.exit_check import check_exit
# conscious agent

# ── palette ────────────────────────────────────────────────────────────────
THEME = Theme({
    "accent":      "#00d4aa",
    "accent_soft": "#008f72",
    "user_tag":    "#7c8cf8",
    "ai_tag":      "#00d4aa",
    "warn":        "#f5a623",
    "success":     "#2ecc71",
    "error":       "#e74c3c",
    "text":        "#e8e8f0",
    "muted":       "#6b6b80",
    "dim":         "#4a4a5a",
    "border":      "#2c2c38",
    "border_lit":  "#3d3d4f",
})

console = Console(theme=THEME, highlight=False)


# ── glyphs ─────────────────────────────────────────────────────────────────
G = {
    "logo":   "▲",
    "user":   "❯",
    "agent":  "●",
    "dot":    "·",
    "check":  "✓",
    "spark":  "✦",
    "arrow":  "›",
    "diamond":"◆",
}


# ── helpers ────────────────────────────────────────────────────────────────
def _box_width() -> int:
    return min(console.width - 4, 96)


def _cwd_label() -> str:
    cwd, home = Path.cwd(), Path.home()
    try:
        return "~/" + str(cwd.relative_to(home))
    except ValueError:
        return str(cwd)


# ── branding ───────────────────────────────────────────────────────────────
def _show_branding():
    lines = [
        "██╗   ██╗██████╗  █████╗ ██╗  ██╗███████╗██╗  ██╗ █████╗",
        "██║   ██║██╔══██╗██╔══██╗██║ ██╔╝██╔════╝██║  ██║██╔══██╗",
        "██║   ██║██████╔╝███████║█████╔╝ ███████╗███████║███████║",
        "╚██╗ ██╔╝██╔══██╗██╔══██║██╔═██╗ ╚════██║██╔══██║██╔══██║",
        " ╚████╔╝ ██║  ██║██║  ██║██║  ██╗███████║██║  ██║██║  ██║",
        "  ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝",
    ]
    shades = ["#00e6b8", "#00d4aa", "#00bf99", "#00a988", "#009377", "#007d65"]
    console.print()
    for line, color in zip(lines, shades):
        console.print(Padding(Text(line, style=f"bold {color}"), (0, 0, 0, 2)))
    console.print()


def _welcome_card(agent: str, user: str):
    """Compact context card — agent identity + session metadata."""
    title = Text.assemble(
        Text(f" {G['logo']} ", style="bold accent"),
        Text(agent.lower(), style="bold text"),
        Text("   A friend who remembers so that you can focus on creating", style="muted"),
    )

    meta = Table.grid(padding=(0, 2), expand=False)
    meta.add_column(style="muted", justify="left", min_width=8)
    meta.add_column(style="text",  justify="left")
    meta.add_row("agent",   f"[bold accent]{agent.lower()}[/bold accent]")
    meta.add_row("user",    f"[user_tag]{user.lower()}[/user_tag]")
    meta.add_row("cwd",     _cwd_label())
    meta.add_row("memory",  f"[success]{G['check']}[/success]  [text]enabled[/text]")

    body = Group(title, Text(""), meta)

    console.print(
        Padding(
            Panel(
                body,
                box=box.ROUNDED,
                border_style="border_lit",
                padding=(1, 3),
                width=_box_width(),
            ),
            (0, 0, 0, 2),
        )
    )

    hints = Text.assemble(
        Text("  type ", style="muted"),
        Text("exit", style="accent"),
        Text(" to save & quit  ", style="muted"),
        Text(G["dot"], style="dim"),
        Text("  ", style="muted"),
        Text("ctrl-c", style="accent"),
        Text(" to abort  ", style="muted"),
        Text(G["dot"], style="dim"),
        Text("  responses render as ", style="muted"),
        Text("markdown", style="accent"),
    )
    console.print(hints)
    console.print()


# ── prompt input (pill) ────────────────────────────────────────────────────
def _ask_prompt(input_prompt: str) -> str:
    """Claude-Code style pill input.

    Top border carries the label; the user types next to a left bar; once
    they press enter we close the pill with a bottom border so the
    completed input reads as a single rounded box on screen.
    """
    width = _box_width()
    label = f" {G['spark']}  {input_prompt} "
    label_len = len(label)
    fill = max(width - label_len - 3, 4)

    top = (
        f"[border_lit]╭─[/border_lit]"
        f"[muted]{label}[/muted]"
        f"[border_lit]{'─' * fill}╮[/border_lit]"
    )
    bottom = f"[border_lit]╰{'─' * (width - 2)}╯[/border_lit]"

    console.print(Padding(top, (1, 0, 0, 2)))
    raw = console.input(
        f"  [border_lit]│[/border_lit]  [bold accent]{G['user']}[/bold accent]  "
    )
    console.print(Padding(bottom, (0, 0, 0, 2)))
    return raw.strip()


# ── response rendering ─────────────────────────────────────────────────────
def _print_response(agent: str, response: str):
    """Minimal, content-first response block — no heavy panel chrome."""
    console.print()

    header = Text.assemble(
        Text("  "),
        Text(f"{G['agent']} ", style="bold ai_tag"),
        Text(agent.lower(), style="bold text"),
        Text(f"   {G['dot']}   ", style="dim"),
        Text("response", style="muted"),
    )
    console.print(header)
    console.print(Padding(Text("│", style="border_lit"), (0, 0, 0, 3)))
    console.print(
        Padding(
            Markdown(response, code_theme="monokai"),
            (0, 0, 0, 5),
        )
    )
    console.print(Padding(Text("│", style="border_lit"), (0, 0, 0, 3)))
    console.print()


def _print_correction(agent: str, response: str):
    """Same shape as a response, but with a success accent."""
    console.print()
    header = Text.assemble(
        Text("  "),
        Text(f"{G['check']} ", style="bold success"),
        Text(agent.lower(), style="bold text"),
        Text(f"   {G['dot']}   ", style="dim"),
        Text("correction applied", style="success"),
    )
    console.print(header)
    console.print(Padding(Text("│", style="success"), (0, 0, 0, 3)))
    console.print(Padding(Markdown(response, code_theme="monokai"), (0, 0, 0, 5)))
    console.print(Padding(Text("│", style="success"), (0, 0, 0, 3)))
    console.print()


def _print_memory_sync(response: str):
    """The end-of-session memory dump — slightly warmer accent."""
    console.print()
    header = Text.assemble(
        Text("  "),
        Text(f"{G['diamond']} ", style="bold warn"),
        Text("memory sync", style="bold text"),
        Text(f"   {G['dot']}   ", style="dim"),
        Text("session committed", style="warn"),
    )
    console.print(header)
    console.print(Padding(Text("│", style="warn"), (0, 0, 0, 3)))
    console.print(Padding(Markdown(response, code_theme="monokai"), (0, 0, 0, 5)))
    console.print(Padding(Text("│", style="warn"), (0, 0, 0, 3)))
    console.print()


# ── core helper ────────────────────────────────────────────────────────────
def _call_and_check(llm_fn, messages, user, agent) -> tuple[str, bool]:
    response = llm_fn(messages)
    should_exit, goodbye = check_exit(response)

    if should_exit:
        with console.status(
            f"[warn]  saving session memory[/warn]",
            spinner="dots",
            spinner_style="warn",
        ):
            messages.append({
                "role": "user",
                "content": "Finalize: summarize session into memory.yaml and update projects.yaml.",
            })
            final = llm_fn(messages)

        _print_memory_sync(final)
        console.print(
            Padding(
                Text.assemble(
                    Text(f"  {G['check']}  ", style="bold success"),
                    Text(goodbye, style="text"),
                ),
                (0, 0, 1, 0),
            )
        )
        return response, True

    return response, False


# ── public entry ───────────────────────────────────────────────────────────
def run_loop(
    title: str,
    input_prompt: str,
    llm_fn,
    verify_always: bool = False,
    trigger_phrase: str = "VERIFICATION_REQUIRED",
    on_verify=None,
):
    agent = agent_name().capitalize()
    user  = user_name().capitalize()
    messages: list[dict] = []

    # ── startup chrome ─────────────────────────────────────────────────────
    _show_branding()
    _welcome_card(agent, user)

    # ── main loop ──────────────────────────────────────────────────────────
    while True:
        prompt = _ask_prompt(input_prompt)

        if not prompt:
            continue

        messages.append({"role": "user", "content": prompt})

        with console.status(
            f"[muted]  {agent.lower()} is thinking[/muted]",
            spinner="dots",
            spinner_style="accent",
        ):
            response, exiting = _call_and_check(llm_fn, messages, user, agent)

        if exiting:
            break

        messages.append({"role": "assistant", "content": response})
        _print_response(agent, response)

        # ── optional verification flow ─────────────────────────────────────
        should_verify = verify_always or trigger_phrase in response

        if should_verify:
            if on_verify:
                on_verify(messages, llm_fn, console)
            else:
                console.print(
                    Padding(
                        Text.assemble(
                            Text(f"  {G['diamond']}  ", style="warn"),
                            Text("was this verdict correct?", style="bold text"),
                        ),
                        (0, 0, 0, 0),
                    )
                )
                is_correct = Prompt.ask(
                    f"  [muted]{G['arrow']}[/muted]",
                    choices=["y", "n", "skip"],
                    default="y",
                    show_choices=True,
                )

                if is_correct == "n":
                    ground_truth = Prompt.ask(
                        f"  [muted]{G['arrow']} ground truth[/muted]",
                        choices=["human", "ai"],
                    )
                    reason = Prompt.ask(
                        f"  [muted]{G['arrow']} why was i wrong[/muted]"
                    )

                    messages.append({
                        "role": "user",
                        "content": (
                            f"WRONG VERDICT. Truth: {ground_truth}. "
                            f"Reason: {reason}. Update memory."
                        ),
                    })

                    with console.status(
                        f"[muted]  applying correction[/muted]",
                        spinner="dots",
                        spinner_style="success",
                    ):
                        correction, exiting = _call_and_check(
                            llm_fn, messages, user, agent
                        )
                    if exiting:
                        break

                    messages.append({"role": "assistant", "content": correction})
                    _print_correction(agent, correction)

                elif is_correct == "y":
                    messages.append({
                        "role": "user",
                        "content": "Verdict confirmed correct. Update validation_benchmarks with PASS.",
                    })

    # ── exit chrome ────────────────────────────────────────────────────────
    console.print()
    farewell = Text.assemble(
        Text(f"  {G['logo']}  ", style="bold accent"),
        Text("session ended  ", style="muted"),
        Text(G["dot"], style="dim"),
        Text(f"  goodbye, ", style="muted"),
        Text(user.lower(), style="bold user_tag"),
    )
    console.print(farewell)
    console.print()
