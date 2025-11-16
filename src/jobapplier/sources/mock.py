"""Mock job source that reads postings from a JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ..profile import CandidateProfile
from .base import ApplicationResult, JobPosting, registry


class MockJobSource:
    name = "mock"

    def __init__(self, path: str | Path = "samples/jobs.json") -> None:
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"Mock jobs file not found: {self.path}")

    def _load_jobs(self) -> list[dict]:
        return json.loads(self.path.read_text())

    def search_jobs(self, profile: CandidateProfile, limit: int = 20) -> List[JobPosting]:
        jobs = []
        for raw in self._load_jobs():
            posting = JobPosting(
                id=str(raw["id"]),
                title=raw["title"],
                company=raw["company"],
                location=raw.get("location", "Remote"),
                description=raw.get("description", ""),
                url=raw.get("url", ""),
                source=self.name,
                metadata=raw,
            )
            if self._matches_profile(posting, profile):
                jobs.append(posting)
            if len(jobs) >= limit:
                break
        return jobs

    def _matches_profile(self, job: JobPosting, profile: CandidateProfile) -> bool:
        text = f"{job.title} {job.description}".lower()
        skills = profile.normalized_skills()
        return any(skill in text for skill in skills) or not skills

    def apply(self, job: JobPosting, profile: CandidateProfile) -> ApplicationResult:
        # Simulated application submission
        message = f"Simulated application submission for {profile.name} to {job.company}"
        return ApplicationResult(job_id=job.id, applied=True, message=message)


registry.register("mock", MockJobSource)
