"""Notification base interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Protocol

from ..profile import CandidateProfile
from ..sources.base import JobPosting


@dataclass
class ApprovalDecision:
    job: JobPosting
    approved: bool
    notes: str | None = None


class BaseNotifier(Protocol):
    def request_approvals(self, jobs: List[JobPosting], profile: CandidateProfile) -> List[ApprovalDecision]:
        ...
