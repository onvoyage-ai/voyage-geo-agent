"""Rich-based progress display helpers for leaderboard flow."""

from __future__ import annotations

from rich.panel import Panel
from rich.table import Table

from voyage_geo.utils.progress import console


def leaderboard_header(category: str, brand_count: int) -> None:
    console.print()
    console.print(
        Panel(
            f"[bold]Category Leaderboard — {brand_count} brands[/bold]",
            title=f"Leaderboard: {category}",
            border_style="blue",
        )
    )


def brand_discovery_status(brands: list[str]) -> None:
    console.print(f"  [green]Discovered {len(brands)} brands:[/green] {', '.join(brands)}")


def analysis_progress(brand: str, index: int, total: int) -> None:
    console.print(f"  [{index}/{total}] Analyzing [cyan]{brand}[/cyan]...")


def print_leaderboard_table(entries: list) -> None:
    """Print a Rich table of leaderboard rankings to terminal."""
    table = Table(
        title="Leaderboard Rankings",
        show_header=True,
        header_style="bold",
        padding=(0, 1),
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Brand", min_width=20)
    table.add_column("Score", width=8, justify="right")
    table.add_column("Mention Rate", width=14, justify="right")
    table.add_column("Mindshare", width=12, justify="right")
    table.add_column("Sentiment", width=12, justify="right")

    for entry in entries:
        sent_color = (
            "green" if entry.sentiment_label == "positive"
            else "red" if entry.sentiment_label == "negative"
            else "dim"
        )
        table.add_row(
            str(entry.rank),
            f"[bold]{entry.brand}[/bold]",
            f"{entry.overall_score:.0f}",
            f"{entry.mention_rate * 100:.0f}%",
            f"{entry.mindshare * 100:.1f}%",
            f"[{sent_color}]{entry.sentiment_score:+.2f}[/{sent_color}]",
        )

    console.print()
    console.print(table)
