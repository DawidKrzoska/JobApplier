"""Profile/CV loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError


class KeywordPreferences(BaseModel):
    must: List[str] = Field(default_factory=list)
    nice: List[str] = Field(default_factory=list)


class LocationPreferences(BaseModel):
    preferred: List[str] = Field(default_factory=list)
    avoid: List[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    name: str
    title: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience_years: Optional[int] = None
    locations: LocationPreferences = Field(default_factory=LocationPreferences)
    keywords: KeywordPreferences = Field(default_factory=KeywordPreferences)
    salary_min: Optional[int] = None
    salary_currency: str = "USD"

    def normalized_skills(self) -> List[str]:
        return [skill.lower() for skill in self.skills]


def load_profile(path: Path | str) -> CandidateProfile:
    """Load and validate the candidate profile YAML."""

    profile_path = Path(path)
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile file not found: {profile_path}")

    raw = yaml.safe_load(profile_path.read_text()) or {}
    try:
        return CandidateProfile.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid profile: {exc}") from exc
