"""Interactive CLI notifier using Rich."""

from __future__ import annotations

from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from ..profile import CandidateProfile
from ..sources.base import JobPosting
from .base import ApprovalDecision, BaseNotifier


class CliNotifier(BaseNotifier):
    def __init__(self) -> None:
        self.console = Console()

    def request_approvals(self, jobs: List[JobPosting], profile: CandidateProfile) -> List[ApprovalDecision]:
        decisions: List[ApprovalDecision] = []
        if not jobs:
            self.console.print("[bold yellow]No new matches found.[/]")
            return decisions

        self.console.print(f"[bold]Found {len(jobs)} potential roles for {profile.name}[/]")

        for idx, job in enumerate(jobs, start=1):
            score = job.metadata.get("score")
            summary_lines = [
                f"[bold]{idx}. {job.title}[/] @ [cyan]{job.company}[/]",
                f"Location: {job.location}",
                f"URL: {job.url or 'N/A'}",
            ]
            if score is not None:
                summary_lines.append(f"Score: {score}")
            summary_lines.append(f"\n{job.description[:400]}...")
            panel = Panel("\n".join(summary_lines), title=f"{job.source.upper()} :: {job.id}")
            self.console.print(panel)

            choice = Prompt.ask("Apply? (y)es / (n)o / (s)kip", choices=["y", "n", "s"], default="s")
            decisions.append(ApprovalDecision(job=job, approved=choice == "y"))

        return decisions
