"""Interactive review checkpoints for the pipeline."""

from __future__ import annotations

from collections import Counter

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from voyage_geo.core.context import RunContext
from voyage_geo.utils.progress import print_query_table

console = Console()

# Fields available for editing (number -> (display_name, attribute_name, is_list))
_EDITABLE_FIELDS: list[tuple[str, str, bool]] = [
    ("Description", "description", False),
    ("Industry", "industry", False),
    ("Category", "category", False),
    ("Competitors", "competitors", True),
    ("Keywords", "keywords", True),
    ("USPs", "unique_selling_points", True),
    ("Target audience", "target_audience", True),
]


def _render_brand_profile(ctx: RunContext) -> Panel:
    """Build a Rich panel displaying the brand profile."""
    p = ctx.brand_profile
    assert p is not None

    lines = Text()
    lines.append("Brand:           ", style="bold")
    lines.append(f"{p.name}\n")
    lines.append("Description:     ", style="bold")
    lines.append(f"{p.description}\n")
    lines.append("Industry:        ", style="bold")
    lines.append(f"{p.industry}\n")
    lines.append("Category:        ", style="bold")
    lines.append(f"{p.category}\n")
    lines.append("\n")
    lines.append("Competitors:     ", style="bold")
    lines.append(f"{' · '.join(p.competitors) if p.competitors else '(none)'}\n")
    lines.append("\n")
    lines.append("Keywords:        ", style="bold")
    lines.append(f"{' · '.join(p.keywords) if p.keywords else '(none)'}\n")
    lines.append("\n")
    lines.append("USPs:            ", style="bold")
    lines.append(f"{' · '.join(p.unique_selling_points) if p.unique_selling_points else '(none)'}\n")
    lines.append("\n")
    lines.append("Target audience: ", style="bold")
    lines.append(f"{' · '.join(p.target_audience) if p.target_audience else '(none)'}\n")

    return Panel(lines, title="Brand Profile", border_style="blue", padding=(1, 2))


async def review_brand_profile(ctx: RunContext) -> RunContext:
    """Interactive review of the brand profile after research stage."""
    if ctx.brand_profile is None:
        return ctx

    while True:
        console.print()
        console.print(_render_brand_profile(ctx))
        console.print()
        console.print(" [bold][c][/bold] Confirm & continue   [bold][e][/bold] Edit a field")
        console.print()

        choice = input("Choice: ").strip().lower()

        if choice == "c":
            return ctx
        elif choice == "e":
            _edit_field(ctx)
        else:
            console.print("[dim]Enter 'c' to confirm or 'e' to edit.[/dim]")


def _edit_field(ctx: RunContext) -> None:
    """Prompt user to pick and edit a brand profile field."""
    p = ctx.brand_profile
    assert p is not None

    console.print()
    # Display field options in a compact grid
    for i, (display_name, _, _) in enumerate(_EDITABLE_FIELDS, 1):
        console.print(f" [bold][{i}][/bold] {display_name}", end="   ")
        if i % 3 == 0:
            console.print()
    console.print()
    console.print()

    raw = input("Field number: ").strip()
    try:
        idx = int(raw) - 1
        if idx < 0 or idx >= len(_EDITABLE_FIELDS):
            raise ValueError
    except ValueError:
        console.print("[red]Invalid field number.[/red]")
        return

    display_name, attr_name, is_list = _EDITABLE_FIELDS[idx]
    current_val = getattr(p, attr_name)

    if is_list:
        console.print(f"Current: {', '.join(current_val) if current_val else '(empty)'}")
        new_raw = input("New value (comma-separated): ").strip()
        if new_raw:
            setattr(p, attr_name, [v.strip() for v in new_raw.split(",") if v.strip()])
            console.print(f"[green]Updated {display_name}[/green]")
    else:
        console.print(f"Current: {current_val or '(empty)'}")
        new_raw = input("New value: ").strip()
        if new_raw:
            setattr(p, attr_name, new_raw)
            console.print(f"[green]Updated {display_name}[/green]")


async def review_queries(ctx: RunContext) -> RunContext:
    """Interactive review of generated queries before execution."""
    if ctx.query_set is None or not ctx.query_set.queries:
        return ctx

    while True:
        console.print()
        print_query_table(ctx.query_set.queries)

        # Summary line
        counts = Counter(q.strategy for q in ctx.query_set.queries)
        parts = [f"{v} {k}" for k, v in sorted(counts.items())]
        total = len(ctx.query_set.queries)
        console.print(f"\n  {total} queries: {' · '.join(parts)}")
        console.print()
        console.print(" [bold][c][/bold] Confirm & start execution   [bold][d][/bold] Remove queries   [bold][a][/bold] Abort")
        console.print()

        choice = input("Choice: ").strip().lower()

        if choice == "c":
            # Sync total_count with actual query list
            ctx.query_set.total_count = len(ctx.query_set.queries)
            return ctx
        elif choice == "d":
            _remove_queries(ctx)
        elif choice == "a":
            raise typer.Abort()
        else:
            console.print("[dim]Enter 'c' to confirm, 'd' to remove queries, or 'a' to abort.[/dim]")


def _remove_queries(ctx: RunContext) -> None:
    """Prompt user to remove specific queries by number."""
    qs = ctx.query_set
    assert qs is not None

    raw = input("Query numbers to remove (comma-separated): ").strip()
    if not raw:
        return

    try:
        indices = {int(x.strip()) for x in raw.split(",") if x.strip()}
    except ValueError:
        console.print("[red]Invalid input — enter numbers separated by commas.[/red]")
        return

    before = len(qs.queries)
    qs.queries = [q for i, q in enumerate(qs.queries, 1) if i not in indices]
    removed = before - len(qs.queries)
    qs.total_count = len(qs.queries)

    if removed:
        console.print(f"[green]Removed {removed} query(ies). {len(qs.queries)} remaining.[/green]")
    else:
        console.print("[dim]No queries matched those numbers.[/dim]")
