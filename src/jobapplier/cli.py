"""Typer-based CLI entrypoint."""

from __future__ import annotations

import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.traceback import install

from .config import AppConfig, load_config
from .profile import CandidateProfile, load_profile
from .workflow import AgentWorkflow, build_context

install()
app = typer.Typer(help="JobApplier agent CLI")
console = Console()


def _resolve(path: Path | None, fallback: str) -> Path:
    return path or Path(fallback)


@app.command()
def run(
    config: Path = typer.Option(Path("samples/config.yaml"), help="Path to config file"),
    profile: Path = typer.Option(Path("samples/profile.yaml"), help="Path to profile file"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable debug logging"),
) -> None:
    """Run a single agent cycle: search jobs, request approval, and apply."""

    try:
        if verbose:
            logging.basicConfig(level=logging.INFO)
        cfg: AppConfig = load_config(config)
        prof: CandidateProfile = load_profile(profile)
        ctx = build_context(cfg, prof)
        AgentWorkflow(ctx).run_once()
    except Exception as exc:  # noqa: BLE001
        console.print(f"[bold red]Error:[/] {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def sources() -> None:
    """List registered job-source adapters."""

    from .sources.base import registry  # lazy import to avoid cycles

    console.print("Available sources:")
    for name in registry.available():
        console.print(f"- {name}")


if __name__ == "__main__":
    app()
