"""Voyage GEO CLI — powered by Typer + Rich."""

from __future__ import annotations

import asyncio

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
        "chatgpt,gemini,claude,perplexity-or,deepseek,grok,llama",
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

    engine = VoyageGeoEngine(config, interactive=interactive, resume_run_id=resume, stop_after=stop_after)
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
        console.print("Set the appropriate env var (e.g. ANTHROPIC_API_KEY) or configure processing.api_key.")
        raise typer.Exit(1)

    proc_config = ProviderConfig(
        name=proc.provider, model=proc.model, api_key=proc.api_key,
        max_tokens=proc.max_tokens, temperature=proc.temperature,
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
        "chatgpt,gemini,claude,perplexity-or,deepseek,grok,llama",
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


@app.command(name="install-skills")
def install_skills(
    target: str = typer.Option(
        "",
        "--target",
        "-t",
        help="Target directory (default: auto-detect OpenClaw or Claude Code)",
    ),
) -> None:
    """Install GEO skills for Claude Code or OpenClaw agents."""
    import shutil
    from importlib.resources import files
    from pathlib import Path

    # Auto-detect target
    if target:
        skill_dir = Path(target)
    elif Path.home().joinpath(".openclaw").is_dir():
        skill_dir = Path.home() / ".openclaw" / "skills"
    else:
        skill_dir = Path(".claude") / "skills"

    # Source skills bundled in the package
    source_dir = Path(str(files("voyage_geo"))) / ".." / ".." / ".claude" / "skills"
    # Fallback: fetch from GitHub if running from pip install (source_dir won't exist)
    if not source_dir.is_dir():
        import urllib.request

        base = "https://raw.githubusercontent.com/Onvoyage-AI/voyage-geo-agent/main/.claude/skills"
        skills = ["geo-run", "geo-leaderboard"]
        console.print(f"Installing skills to [bold]{skill_dir}[/bold] ...\n")
        for name in skills:
            dest = skill_dir / name
            dest.mkdir(parents=True, exist_ok=True)
            url = f"{base}/{name}/SKILL.md"
            urllib.request.urlretrieve(url, dest / "SKILL.md")
            console.print(f"  [green]+[/green] {name}")
    else:
        source_dir = source_dir.resolve()
        console.print(f"Installing skills to [bold]{skill_dir}[/bold] ...\n")
        for src in sorted(source_dir.iterdir()):
            if src.is_dir() and src.name.startswith("geo-"):
                dest = skill_dir / src.name
                dest.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src / "SKILL.md", dest / "SKILL.md")
                console.print(f"  [green]+[/green] {src.name}")

    console.print(f"\n[bold green]Done![/bold green] Skills installed to {skill_dir}")
    console.print("\nCommands: /geo-run  /geo-leaderboard")


@app.command()
def version() -> None:
    """Show version."""
    console.print(f"voyage-geo v{__version__}")


if __name__ == "__main__":
    app()
