"""Base interfaces for job-source connectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Protocol

from ..profile import CandidateProfile


@dataclass
class JobPosting:
    id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApplicationResult:
    job_id: str
    applied: bool
    message: str = ""


class JobSourceAdapter(Protocol):
    """Protocol describing a job source."""

    name: str

    def search_jobs(self, profile: CandidateProfile, limit: int = 20) -> List[JobPosting]:
        ...

    def apply(self, job: JobPosting, profile: CandidateProfile) -> ApplicationResult:
        ...


class JobSourceRegistry:
    """Registry mapping adapter names to constructors."""

    def __init__(self) -> None:
        self._registry: Dict[str, Any] = {}

    def register(self, key: str, factory: Any) -> None:
        self._registry[key] = factory

    def create(self, key: str, **options: Any) -> JobSourceAdapter:
        if key not in self._registry:
            raise ValueError(f"Unknown job source adapter '{key}'")
        return self._registry[key](**options)

    def available(self) -> Iterable[str]:
        return self._registry.keys()


registry = JobSourceRegistry()
