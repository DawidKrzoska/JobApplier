"""Simple heuristic-based scoring for job matches."""

from __future__ import annotations

import math
import re
from typing import Dict, Iterable

from .profile import CandidateProfile
from .sources.base import JobPosting


DEFAULT_WEIGHTS = {
    "skill": 4.0,
    "keyword": 3.0,
    "location": 2.0,
    "title": 1.5,
}


def tokenize(text: str | None) -> Iterable[str]:
    if not text:
        return []
    return re.findall(r"[a-zA-Z0-9#+\-]+", text.lower())


def score_job(job: JobPosting, profile: CandidateProfile, weights: Dict[str, float] | None = None) -> float:
    weights = {**DEFAULT_WEIGHTS, **(weights or {})}

    description_tokens = set(tokenize(job.description))
    title_tokens = set(tokenize(job.title))
    skill_score = sum(weights["skill"] for skill in profile.normalized_skills() if skill in description_tokens or skill in title_tokens)

    keyword_score = 0.0
    for kw in profile.keywords.must:
        if kw.lower() in description_tokens:
            keyword_score += weights["keyword"]
        else:
            keyword_score -= weights["keyword"]  # penalize missing must-haves
    for kw in profile.keywords.nice:
        if kw.lower() in description_tokens:
            keyword_score += weights["keyword"] * 0.5

    location_score = 0.0
    if profile.locations.preferred:
        if any(loc.lower() in job.location.lower() for loc in profile.locations.preferred):
            location_score = weights["location"]
        elif any(loc.lower() in job.location.lower() for loc in profile.locations.avoid):
            location_score = -weights["location"]

    title_score = sum(weights["title"] for kw in profile.normalized_skills() if kw in title_tokens)

    total = skill_score + keyword_score + location_score + title_score
    return round(total, 2)


def rank_jobs(jobs: list[JobPosting], profile: CandidateProfile, weights: Dict[str, float] | None = None) -> list[JobPosting]:
    return sorted(jobs, key=lambda job: score_job(job, profile, weights), reverse=True)
