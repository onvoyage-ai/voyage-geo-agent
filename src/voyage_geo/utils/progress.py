"""Rich-based progress and display helpers."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


def stage_header(name: str, description: str) -> None:
    console.print()
    console.print(Panel(f"[bold]{description}[/bold]", title=f"Stage: {name}", border_style="blue"))


def create_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )


def print_query_table(queries: list) -> None:  # list[GeneratedQuery]
    table = Table(show_header=True, header_style="bold dim", padding=(0, 1))
    table.add_column("#", style="dim", width=4)
    table.add_column("Strategy", width=12)
    table.add_column("Category", width=16)
    table.add_column("Query", min_width=50)

    strategy_colors = {
        "keyword": "cyan",
        "persona": "magenta",
        "competitor": "yellow",
        "intent": "green",
        "discovery": "bright_cyan",
        "vertical": "bright_magenta",
        "direct-rec": "bright_cyan",
        "comparison": "bright_yellow",
        "scenario": "bright_green",
    }

    for i, q in enumerate(queries, 1):
        color = strategy_colors.get(q.strategy, "white")
        text = q.text if len(q.text) <= 80 else q.text[:77] + "..."
        table.add_row(
            str(i),
            f"[{color}]{q.strategy}[/{color}]",
            q.category,
            text,
        )

    console.print(table)
