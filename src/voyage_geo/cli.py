"""Voyage GEO CLI — powered by Typer + Rich."""

from __future__ import annotations

import asyncio
import json
from datetime import date

import typer
from rich.console import Console
from rich.table import Table

from voyage_geo import __version__

app = typer.Typer(
    name="voyage-geo",
    help="Open source Generative Engine Optimization (GEO) analysis tool",
    no_args_is_help=True,
)
console = Console()


@app.command()
def run(
    brand: str = typer.Option(..., "--brand", "-b", help="Brand name to analyze"),
    website: str | None = typer.Option(None, "--website", "-w", help="Brand website URL"),
    providers: str = typer.Option(
        "chatgpt,gemini,claude,perplexity-or,deepseek,grok,llama,mistral,cohere,qwen,kimi,glm",
        "--providers",
        "-p",
        help="Comma-separated provider names",
    ),
    queries: int = typer.Option(20, "--queries", "-q", help="Number of queries to generate"),
    iterations: int = typer.Option(1, "--iterations", "-i", help="Iterations per query"),
    formats: str = typer.Option("html,json", "--formats", "-f", help="Report formats (html,json,csv,markdown)"),
    concurrency: int = typer.Option(10, "--concurrency", "-c", help="Concurrent API requests"),
    output_dir: str = typer.Option("./data/runs", "--output-dir", "-o", help="Output directory"),
    processing_provider: str | None = typer.Option(None, "--processing-provider", help="Provider for non-execution LLM calls (default: anthropic)"),
    processing_model: str | None = typer.Option(None, "--processing-model", help="Model for non-execution LLM calls (default: claude-opus-4-6)"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", help="Interactive review checkpoints after research & query generation"),
    as_of_date: str | None = typer.Option(None, "--as-of-date", help="Logical run date (YYYY-MM-DD) for trend tracking"),
    resume: str | None = typer.Option(None, "--resume", "-r", help="Resume from an existing run ID (skips research, reuses brand profile)"),
    stop_after: str | None = typer.Option(None, "--stop-after", help="Stop pipeline after this stage (e.g. research, query-generation)"),
) -> None:
    """Run full GEO analysis pipeline."""
    from voyage_geo.config.loader import load_config

    overrides: dict = {
        "brand": brand,
        "website": website,
        "queries": {"count": queries},
        "execution": {"concurrency": concurrency, "iterations": iterations},
        "report": {"formats": formats.split(",")},
        "output_dir": output_dir,
    }

    # Apply processing model overrides
    processing_overrides: dict = {}
    if processing_provider:
        processing_overrides["provider"] = processing_provider
    if processing_model:
        processing_overrides["model"] = processing_model
    if processing_overrides:
        overrides["processing"] = processing_overrides

    config = load_config(overrides=overrides)

    # Filter providers
    requested = [p.strip() for p in providers.split(",")]
    for name in list(config.providers.keys()):
        if name not in requested:
            config.providers[name].enabled = False

    enabled = [n for n, p in config.providers.items() if p.enabled and p.api_key]
    if not enabled:
        console.print("[red]No providers configured with API keys.[/red]")
        console.print("Set OPENROUTER_API_KEY for all models, or individual keys: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, PERPLEXITY_API_KEY")
        raise typer.Exit(1)

    console.print(f"\n[bold blue]Voyage GEO[/bold blue] v{__version__}")
    console.print(f"Brand: [bold]{brand}[/bold]")
    console.print(f"Providers: {', '.join(enabled)}")
    console.print(f"Queries: {queries} | Iterations: {iterations} | Concurrency: {concurrency}\n")

    from voyage_geo.core.engine import VoyageGeoEngine

    if as_of_date:
        try:
            date.fromisoformat(as_of_date)
        except ValueError:
            console.print("[red]Invalid --as-of-date. Use YYYY-MM-DD.[/red]")
            raise typer.Exit(1)

    # Validate resume run exists
    if resume:
        from voyage_geo.storage.filesystem import FileSystemStorage
        _storage = FileSystemStorage(output_dir)
        if not _storage.run_dir(resume).exists():
            console.print(f"[red]Run not found:[/red] {resume}")
            available = _storage.list_runs()
            if available:
                console.print(f"Available runs: {', '.join(available[:5])}")
            raise typer.Exit(1)

    engine = VoyageGeoEngine(
        config,
        interactive=interactive,
        resume_run_id=resume,
        stop_after=stop_after,
        as_of_date=as_of_date,
    )
    result = asyncio.run(engine.run())

    if result.analysis_result:
        a = result.analysis_result
        console.print()
        console.print("[bold green]Analysis Complete[/bold green]")
        console.print(f"  Score: [bold]{a.summary.overall_score}/100[/bold]")
        console.print(f"  {a.summary.headline}")
        console.print(f"  Run: {result.run_id}")
        report_path = f"{output_dir}/{result.run_id}/reports/report.html"
        console.print(f"  Report: [link=file://{report_path}]{report_path}[/link]")


@app.command(name="providers")
def list_providers(
    test: bool = typer.Option(False, "--test", "-t", help="Run health checks"),
) -> None:
    """List and test configured providers."""
    from voyage_geo.config.loader import load_config

    config = load_config()

    table = Table(title="Providers", show_header=True, header_style="bold")
    table.add_column("Name")
    table.add_column("API Key")
    table.add_column("Model")
    table.add_column("Status")

    for name, pconfig in config.providers.items():
        has_key = "set" if pconfig.api_key else "[red]missing[/red]"
        model = pconfig.model or "default"
        status = "[green]enabled[/green]" if pconfig.enabled else "[dim]disabled[/dim]"
        table.add_row(name, has_key, model, status)

    console.print(table)

    # Show processing provider status
    proc = config.processing
    if proc.api_key:
        console.print(f"\nProcessing provider: [bold]{proc.provider}[/bold] ({proc.model}) — [green]configured[/green]")
    else:
        console.print(f"\nProcessing provider: [bold]{proc.provider}[/bold] ({proc.model}) — [red]NOT CONFIGURED[/red]")
        console.print("  Set ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, or OPENROUTER_API_KEY")

    if test:
        console.print("\nRunning health checks...")
        from voyage_geo.providers.registry import ProviderRegistry

        registry = ProviderRegistry()
        for name, pconfig in config.providers.items():
            if pconfig.enabled and pconfig.api_key:
                registry.register(name, pconfig)

        async def _check():
            for provider in registry.get_enabled():
                result = await provider.health_check()
                if result["healthy"]:
                    console.print(f"  [green]OK[/green] {provider.name} ({result['latency_ms']}ms)")
                else:
                    console.print(f"  [red]FAIL[/red] {provider.name}: {result.get('error', 'unknown')}")

        asyncio.run(_check())


@app.command()
def research(
    brand: str = typer.Argument(..., help="Brand name to research"),
    website: str | None = typer.Option(None, "--website", "-w", help="Brand website URL to scrape"),
    output_dir: str = typer.Option("./data/runs", "--output-dir", "-o", help="Output directory"),
) -> None:
    """Research a brand — build a profile from AI + web scraping."""
    from voyage_geo.config.loader import load_config
    from voyage_geo.config.schema import ProviderConfig
    from voyage_geo.core.context import create_run_context
    from voyage_geo.providers.registry import create_provider
    from voyage_geo.stages.research.stage import ResearchStage
    from voyage_geo.storage.filesystem import FileSystemStorage

    config = load_config(overrides={"brand": brand, "website": website, "output_dir": output_dir})

    # Create processing provider
    proc = config.processing
    if not proc.api_key:
        console.print(f"[red]No API key found for processing provider '{proc.provider}'.[/red]")
        console.print("Set one of: ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, or OPENROUTER_API_KEY")
        raise typer.Exit(1)

    proc_config = ProviderConfig(
        name=proc.provider, model=proc.model, api_key=proc.api_key,
        base_url=proc.base_url, max_tokens=proc.max_tokens,
    )
    proc_provider = create_provider(proc.provider, proc_config)
    storage = FileSystemStorage(config.output_dir)

    console.print(f"\n[bold blue]Voyage GEO[/bold blue] v{__version__}")
    console.print(f"Researching: [bold]{brand}[/bold]")
    if website:
        console.print(f"Website: {website}\n")

    async def _run():
        ctx = create_run_context(config)
        await storage.create_run_dir(ctx.run_id)
        stage = ResearchStage(proc_provider, storage)
        ctx = await stage.execute(ctx)
        return ctx

    ctx = asyncio.run(_run())
    if ctx.brand_profile:
        p = ctx.brand_profile
        console.print(f"\n[bold green]Brand Profile Built[/bold green]")
        console.print(f"  Name: {p.name}")
        console.print(f"  Industry: {p.industry}")
        console.print(f"  Category: {p.category}")
        console.print(f"  Competitors: {', '.join(p.competitors[:5])}")
        console.print(f"  Keywords: {', '.join(p.keywords[:5])}")
        console.print(f"  Saved to: {config.output_dir}/{ctx.run_id}/brand-profile.json")


@app.command()
def report(
    run_id: str = typer.Option(..., "--run-id", "-r", help="Run ID to generate report from"),
    formats: str = typer.Option("html,json", "--formats", "-f", help="Report formats (html,json,csv,markdown)"),
    output_dir: str = typer.Option("./data/runs", "--output-dir", "-o", help="Output directory"),
) -> None:
    """Generate reports from an existing run."""
    from voyage_geo.config.loader import load_config
    from voyage_geo.core.context import RunContext
    from voyage_geo.stages.reporting.stage import ReportingStage
    from voyage_geo.storage.filesystem import FileSystemStorage
    from voyage_geo.types.analysis import AnalysisResult

    config = load_config(overrides={"report": {"formats": formats.split(",")}, "output_dir": output_dir})
    storage = FileSystemStorage(config.output_dir)

    # Check run exists
    run_dir = storage.run_dir(run_id)
    if not run_dir.exists():
        console.print(f"[red]Run not found:[/red] {run_id}")
        console.print(f"Looking in: {run_dir}")
        available = storage.list_runs()
        if available:
            console.print(f"Available runs: {', '.join(available[:5])}")
        raise typer.Exit(1)

    console.print(f"\n[bold blue]Voyage GEO[/bold blue] v{__version__}")
    console.print(f"Generating reports for run: [bold]{run_id}[/bold]")
    console.print(f"Formats: {formats}\n")

    async def _run():
        analysis_data = await storage.load_json(run_id, "analysis/analysis.json")
        if not analysis_data:
            console.print("[red]No analysis data found for this run.[/red]")
            raise typer.Exit(1)

        analysis = AnalysisResult(**analysis_data)
        ctx = RunContext(run_id=run_id, config=config, started_at="", analysis_result=analysis)
        stage = ReportingStage(storage)
        await stage.execute(ctx)

    asyncio.run(_run())
    console.print(f"\n[bold green]Reports generated:[/bold green] {run_dir / 'reports'}")


@app.command()
def leaderboard(
    category: str = typer.Argument(..., help="Category to analyze (e.g. 'top vc', 'best CRM tools')"),
    providers: str = typer.Option(
        "chatgpt,gemini,claude,perplexity-or,deepseek,grok,llama,mistral,cohere,qwen,kimi,glm",
        "--providers",
        "-p",
        help="Comma-separated provider names",
    ),
    queries: int = typer.Option(20, "--queries", "-q", help="Number of queries to generate"),
    formats: str = typer.Option("html,json", "--formats", "-f", help="Report formats (html,json,csv,markdown)"),
    concurrency: int = typer.Option(10, "--concurrency", "-c", help="Concurrent API requests"),
    output_dir: str = typer.Option("./data/runs", "--output-dir", "-o", help="Output directory"),
    max_brands: int = typer.Option(50, "--max-brands", help="Max brands to extract from AI responses"),
    processing_provider: str | None = typer.Option(None, "--processing-provider", help="Provider for non-execution LLM calls"),
    processing_model: str | None = typer.Option(None, "--processing-model", help="Model for non-execution LLM calls"),
    stop_after: str | None = typer.Option(None, "--stop-after", help="Stop after stage (e.g. query-generation) for review"),
    resume: str | None = typer.Option(None, "--resume", "-r", help="Resume from an existing leaderboard run ID"),
) -> None:
    """Run category-wide leaderboard — compare all brands in a category."""
    from voyage_geo.config.loader import load_config

    overrides: dict = {
        "queries": {"count": queries},
        "execution": {"concurrency": concurrency},
        "report": {"formats": formats.split(",")},
        "output_dir": output_dir,
    }

    # Apply processing model overrides
    processing_overrides: dict = {}
    if processing_provider:
        processing_overrides["provider"] = processing_provider
    if processing_model:
        processing_overrides["model"] = processing_model
    if processing_overrides:
        overrides["processing"] = processing_overrides

    config = load_config(overrides=overrides)

    # Filter providers
    requested = [p.strip() for p in providers.split(",")]
    for name in list(config.providers.keys()):
        if name not in requested:
            config.providers[name].enabled = False

    enabled = [n for n, p in config.providers.items() if p.enabled and p.api_key]
    if not enabled:
        console.print("[red]No providers configured with API keys.[/red]")
        console.print("Set OPENROUTER_API_KEY for all models, or individual keys: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, PERPLEXITY_API_KEY")
        raise typer.Exit(1)

    console.print(f"\n[bold blue]Voyage GEO[/bold blue] v{__version__}")
    console.print(f"Category: [bold]{category}[/bold]")
    console.print(f"Brands: extracted from AI responses (max {max_brands})")
    console.print(f"Providers: {', '.join(enabled)}")
    console.print(f"Queries: {queries} | Concurrency: {concurrency}\n")

    from voyage_geo.core.leaderboard_engine import LeaderboardEngine

    # Validate resume run exists
    if resume:
        from voyage_geo.storage.filesystem import FileSystemStorage
        _storage = FileSystemStorage(output_dir)
        if not _storage.run_dir(resume).exists():
            console.print(f"[red]Run not found:[/red] {resume}")
            available = _storage.list_runs()
            if available:
                console.print(f"Available runs: {', '.join(available[:5])}")
            raise typer.Exit(1)

    engine = LeaderboardEngine(
        config,
        category,
        max_brands=max_brands,
        report_formats=formats.split(","),
        stop_after=stop_after,
        resume_run_id=resume,
    )
    result = asyncio.run(engine.run())

    console.print()
    console.print("[bold green]Leaderboard Complete[/bold green]")
    console.print(f"  Category: {category}")
    console.print(f"  Brands: {len(result.brands)}")
    console.print(f"  #1: [bold]{result.entries[0].brand}[/bold] ({result.entries[0].overall_score:.0f}/100)" if result.entries else "")
    console.print(f"  Run: {result.run_id}")
    report_path = f"{output_dir}/{result.run_id}/reports/leaderboard.html"
    console.print(f"  Report: [link=file://{report_path}]{report_path}[/link]")


@app.command(name="leaderboard-report")
def leaderboard_report(
    run_id: str = typer.Option(..., "--run-id", "-r", help="Leaderboard run ID"),
    formats: str = typer.Option("html,json", "--formats", "-f", help="Report formats (html,json,csv,markdown)"),
    output_dir: str = typer.Option("./data/runs", "--output-dir", "-o", help="Output directory"),
) -> None:
    """Regenerate leaderboard reports from an existing run."""
    from voyage_geo.stages.reporting.leaderboard_renderer import LeaderboardRenderer
    from voyage_geo.storage.filesystem import FileSystemStorage

    storage = FileSystemStorage(output_dir)

    # Check run exists
    run_dir = storage.run_dir(run_id)
    if not run_dir.exists():
        console.print(f"[red]Run not found:[/red] {run_id}")
        available = storage.list_runs()
        if available:
            console.print(f"Available runs: {', '.join(available[:5])}")
        raise typer.Exit(1)

    console.print(f"\n[bold blue]Voyage GEO[/bold blue] v{__version__}")
    console.print(f"Regenerating reports for leaderboard run: [bold]{run_id}[/bold]")
    console.print(f"Formats: {formats}\n")

    fmt_list = [f.strip() for f in formats.split(",")]

    async def _run():
        renderer, lb_result, exec_run, query_set = await LeaderboardRenderer.from_disk(storage, run_id)
        await renderer.render(run_id, lb_result, fmt_list, exec_run, query_set)

    asyncio.run(_run())
    console.print(f"\n[bold green]Reports regenerated:[/bold green] {run_dir / 'reports'}")


@app.command()
def runs(
    output_dir: str = typer.Option("./data/runs", "--output-dir", "-o", help="Output directory"),
) -> None:
    """List past analysis runs."""
    import json
    from voyage_geo.storage.filesystem import FileSystemStorage

    storage = FileSystemStorage(output_dir)
    run_list = storage.list_runs()

    if not run_list:
        console.print("[dim]No runs found.[/dim]")
        return

    table = Table(title="Past Runs", show_header=True, header_style="bold")
    table.add_column("Run ID")
    table.add_column("Type")
    table.add_column("Brand / Category")
    table.add_column("Status")
    table.add_column("Date")

    for rid in run_list[:20]:
        meta_path = storage.run_dir(rid) / "metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
            run_type = meta.get("type", "analysis")
            label = meta.get("category", meta.get("brand", "—"))
            table.add_row(rid, run_type, label, meta.get("status", "—"), meta.get("started_at", "—")[:19])
        else:
            table.add_row(rid, "—", "—", "—", "—")

    console.print(table)


@app.command(name="trends-index")
def trends_index(
    output_dir: str = typer.Option("./data/runs", "--output-dir", "-o", help="Run output directory"),
    out_file: str = typer.Option("./data/trends/snapshots.json", "--out-file", help="Destination JSON file"),
    brand: str | None = typer.Option(None, "--brand", "-b", help="Filter by brand"),
) -> None:
    """Build a trend index from analysis snapshots."""
    from voyage_geo.trends import collect_trend_records, write_trend_index

    records = collect_trend_records(output_dir, brand=brand)
    path = write_trend_index(records, out_file)
    console.print(f"[green]Wrote {len(records)} records[/green] to {path}")


@app.command()
def trends(
    brand: str = typer.Option(..., "--brand", "-b", help="Brand to chart over time"),
    output_dir: str = typer.Option("./data/runs", "--output-dir", "-o", help="Run output directory"),
    metric: str = typer.Option(
        "overall_score",
        "--metric",
        help="Metric: overall_score, mention_rate, mindshare, sentiment_score, share_of_voice_top5, mindshare_gap_to_leader, mention_rate_gap_to_leader",
    ),
    compare: str | None = typer.Option(None, "--compare", help="Comma-separated competitor names"),
    as_json: bool = typer.Option(False, "--json", help="Print JSON payload"),
) -> None:
    """Show trend data for a brand, including competitor-relative metrics."""
    from voyage_geo.trends import build_competitor_series, collect_trend_records

    records = collect_trend_records(output_dir, brand=brand)
    if not records:
        console.print(f"[dim]No trend records found for brand: {brand}[/dim]")
        raise typer.Exit(0)

    allowed = {
        "overall_score",
        "mention_rate",
        "mindshare",
        "sentiment_score",
        "share_of_voice_top5",
        "mindshare_gap_to_leader",
        "mention_rate_gap_to_leader",
    }
    if metric not in allowed:
        console.print(f"[red]Invalid --metric:[/red] {metric}")
        console.print(f"Allowed: {', '.join(sorted(allowed))}")
        raise typer.Exit(1)

    comp_names = [c.strip() for c in compare.split(",")] if compare else None

    series = []
    for record in records:
        rel = record.get("competitor_relative", {}) or {}
        value = record.get(metric)
        if metric == "share_of_voice_top5":
            value = rel.get("share_of_voice_top5", 0.0)
        elif metric == "mindshare_gap_to_leader":
            value = rel.get("mindshare_gap_to_leader", 0.0)
        elif metric == "mention_rate_gap_to_leader":
            value = rel.get("mention_rate_gap_to_leader", 0.0)
        series.append({
            "as_of_date": record.get("as_of_date", ""),
            "run_id": record.get("run_id", ""),
            "value": value,
            "leader_brand": rel.get("leader_brand", ""),
            "brand_rank": rel.get("brand_rank", 0),
        })

    competitors = build_competitor_series(records, comp_names)

    if as_json:
        console.print(json.dumps({
            "brand": brand,
            "metric": metric,
            "series": series,
            "competitors": competitors,
        }, indent=2))
        return

    table = Table(title=f"Trends: {brand}", show_header=True, header_style="bold")
    table.add_column("Date")
    table.add_column("Run ID")
    table.add_column(metric)
    table.add_column("Rank")
    table.add_column("Leader")
    for item in series:
        value = item["value"]
        if isinstance(value, float):
            shown = f"{value:.4f}"
        else:
            shown = str(value)
        table.add_row(
            str(item["as_of_date"]),
            str(item["run_id"]),
            shown,
            str(item["brand_rank"]),
            str(item["leader_brand"]),
        )
    console.print(table)

    if competitors:
        comp_table = Table(title="Competitor Series", show_header=True, header_style="bold")
        comp_table.add_column("Competitor")
        comp_table.add_column("Points")
        comp_table.add_column("Latest Mindshare")
        comp_table.add_column("Latest Mention Rate")
        for name, values in sorted(competitors.items()):
            latest = values[-1]
            comp_table.add_row(
                name,
                str(len(values)),
                f"{float(latest.get('mindshare', 0.0)):.4f}",
                f"{float(latest.get('mention_rate', 0.0)):.4f}",
            )
        console.print(comp_table)


@app.command(name="trends-dashboard")
def trends_dashboard(
    brand: str = typer.Option(..., "--brand", "-b", help="Brand to visualize"),
    output_dir: str = typer.Option("./data/runs", "--output-dir", "-o", help="Run output directory"),
    out_file: str | None = typer.Option(None, "--out-file", help="HTML output path"),
    compare: str | None = typer.Option(None, "--compare", help="Comma-separated competitor names"),
) -> None:
    """Generate an HTML trends dashboard for one brand."""
    from voyage_geo.trends import collect_trend_records
    from voyage_geo.trends_dashboard import write_dashboard

    records = collect_trend_records(output_dir, brand=brand)
    if not records:
        console.print(f"[dim]No trend records found for brand: {brand}[/dim]")
        raise typer.Exit(0)

    comp_names = [c.strip() for c in compare.split(",")] if compare else None
    path = write_dashboard(brand, output_dir, out_file=out_file, compare=comp_names)
    console.print(f"[green]Dashboard generated:[/green] {path}")


@app.command(name="app")
def app_mode(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(8765, "--port", help="Bind port"),
    output_dir: str = typer.Option("./data/runs", "--output-dir", "-o", help="Run output directory"),
) -> None:
    """Start optional local GUI + API mode."""
    try:
        import uvicorn  # type: ignore
    except Exception:
        console.print("[red]App mode requires FastAPI/Uvicorn.[/red]")
        console.print("Install with: [bold]pip install 'voyage-geo[app]'[/bold]")
        raise typer.Exit(1)

    from voyage_geo.app.server import create_app

    server_app = create_app(output_dir=output_dir)
    console.print(f"[bold green]Starting app mode[/bold green] on http://{host}:{port}")
    uvicorn.run(server_app, host=host, port=port, log_level="info")


@app.command()
def version() -> None:
    """Show version."""
    console.print(f"voyage-geo v{__version__}")


if __name__ == "__main__":
    app()
