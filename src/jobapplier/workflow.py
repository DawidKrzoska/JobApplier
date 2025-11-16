"""Core orchestration workflow for the JobApplier agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .config import AppConfig
from .notifiers.base import BaseNotifier
from .profile import CandidateProfile
from .scoring import rank_jobs, score_job
from .sources.base import JobPosting, JobSourceAdapter, registry
from .storage import JsonStateStore

# Ensure built-in adapters get registered.
from .sources import linkedin as _linkedin  # noqa: F401
from .notifiers.cli import CliNotifier


@dataclass
class AgentContext:
    config: AppConfig
    profile: CandidateProfile
    sources: List[JobSourceAdapter]
    notifier: BaseNotifier
    store: JsonStateStore


class AgentWorkflow:
    def __init__(self, ctx: AgentContext) -> None:
        self.ctx = ctx

    def collect_jobs(self) -> List[JobPosting]:
        collected: List[JobPosting] = []
        for source in self.ctx.sources:
            for job in source.search_jobs(self.ctx.profile):
                if self.ctx.store.has_seen(job.id):
                    continue
                collected.append(job)
        return collected

    def run_once(self) -> None:
        jobs = self.collect_jobs()
        if not jobs:
            self.ctx.notifier.request_approvals([], self.ctx.profile)
            return

        for job in jobs:
            score = score_job(job, self.ctx.profile, self.ctx.config.scoring)
            job.metadata["score"] = score
            self.ctx.store.record_seen(job.id, {"score": score, "source": job.source})

        min_score = float(self.ctx.config.approvals.get("min_score", 0))
        filtered = [job for job in jobs if job.metadata.get("score", 0) >= min_score]
        ranked = rank_jobs(filtered, self.ctx.profile, self.ctx.config.scoring)

        approvals = self.ctx.notifier.request_approvals(ranked, self.ctx.profile)

        for decision in approvals:
            if not decision.approved:
                continue
            source = next((s for s in self.ctx.sources if s.name == decision.job.source), None)
            if not source:
                continue
            result = source.apply(decision.job, self.ctx.profile)
            status = "applied" if result.applied else "failed"
            self.ctx.store.record_application(decision.job.id, status, result.message)


def build_notifier(channel: str) -> BaseNotifier:
    if channel == "cli":
        return CliNotifier()
    raise ValueError(f"Unsupported notifier channel '{channel}'")


def build_sources(config: AppConfig) -> List[JobSourceAdapter]:
    sources: List[JobSourceAdapter] = []
    for src in config.job_sources:
        adapter = registry.create(src.type, **src.options)
        sources.append(adapter)
    return sources


def build_context(config: AppConfig, profile: CandidateProfile) -> AgentContext:
    store = JsonStateStore(config.storage.path)
    notifier = build_notifier(config.notifications.channel)
    sources = build_sources(config)
    return AgentContext(config=config, profile=profile, sources=sources, notifier=notifier, store=store)
