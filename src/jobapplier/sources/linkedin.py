"""LinkedIn job search adapter."""

from __future__ import annotations

import logging
import re
from typing import List

import httpx
from bs4 import BeautifulSoup, Tag

from ..profile import CandidateProfile
from .base import ApplicationResult, JobPosting, registry

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class LinkedInJobSource:
    """Fetch job postings from LinkedIn public search pages."""

    name = "linkedin"

    def __init__(
        self,
        keywords: str,
        location: str | None = None,
        limit: int = 25,
        remote: bool | None = None,
        experience_level: str | None = None,
        session_cookie: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        if not keywords:
            raise ValueError("LinkedIn adapter requires a keywords string.")
        self.keywords = keywords
        self.location = location
        self.limit = limit
        self.remote = remote
        self.experience_level = experience_level
        self.timeout = timeout

        headers = {"user-agent": USER_AGENT}
        cookies = {}
        if session_cookie:
            # Enables authenticated search result volumes.
            cookies["li_at"] = session_cookie

        self.client = httpx.Client(
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            follow_redirects=True,
        )

    def _params(self, start: int) -> dict:
        params: dict = {"keywords": self.keywords, "start": start}
        if self.location:
            params["location"] = self.location
        if self.remote is True:
            params["f_WT"] = "2"  # LinkedIn filter for remote roles
        elif self.remote is False:
            params["f_WT"] = "1"
        if self.experience_level:
            params["f_E"] = self.experience_level
        return params

    def _fetch_page(self, start: int) -> str:
        response = self.client.get(SEARCH_URL, params=self._params(start))
        response.raise_for_status()
        return response.text

    def _parse_jobs(self, html: str) -> List[JobPosting]:
        clean_html = html.replace("<!--", "").replace("-->", "")
        soup = BeautifulSoup(clean_html, "html.parser")
        jobs: List[JobPosting] = []
        seen_ids: set[str] = set()

        selectors = "a.base-card__full-link, a.job-card-container__link, a.job-card-list__title, a.result-card__full-card-link"
        links = soup.select(selectors)
        cards = soup.select(
            "li.jobs-search-results__list-item, div.base-card[data-entity-urn], li.job-card-container"
        )
        logger.info(
            "LinkedIn parser candidates: links=%s cards=%s html_len=%s",
            len(links),
            len(cards),
            len(clean_html),
        )

        for card in cards:
            job_id = (
                card.get("data-occludable-job-id")
                or card.get("data-id")
                or card.get("data-entity-urn", "").split(":")[-1]
                or card.get("data-job-id")
            )
            if not job_id or job_id in seen_ids:
                continue
            link = card.select_one(selectors)
            url = ""
            if link and link.has_attr("href"):
                url = link["href"].split("?")[0]
                if not job_id:
                    job_id = self._extract_job_id(url, link)
            if not job_id or job_id in seen_ids:
                continue
            title = self._first_text(
                card,
                [".base-search-card__title", ".job-card-list__title", ".sr-only"],
            )
            company = self._first_text(
                card,
                [
                    ".base-search-card__subtitle",
                    ".job-card-container__primary-description",
                    ".hidden-nested-link",
                ],
            )
            location = self._first_text(
                card,
                [".job-search-card__location", ".job-card-container__metadata-item"],
            )
            description = self._first_text(
                card,
                [
                    ".base-search-card__snippet",
                    ".job-card-container__metadata-item--bullet",
                    ".job-card-container__metadata-wrapper",
                ],
            ) or "LinkedIn job listing"
            if not title or not company:
                logger.debug(
                    "LinkedIn skipping structured card job_id=%s missing=%s",
                    job_id,
                    "title" if not title else "company",
                )
                continue
            seen_ids.add(job_id)
            jobs.append(
                JobPosting(
                    id=job_id,
                    title=title.strip(),
                    company=company.strip(),
                    location=(location or "").strip(),
                    description=description.strip(),
                    url=url,
                    source=self.name,
                    metadata={"raw_id": job_id},
                )
            )
        if jobs:
            logger.info("LinkedIn parsed %s structured jobs", len(jobs))
            return jobs

        for link in links:
            url = link.get("href", "").split("?")[0]
            job_id = self._extract_job_id(url, link)
            if not job_id or job_id in seen_ids:
                continue

            card = link.find_parent("li") or link.find_parent("div", class_="base-card") or link.parent
            title = link.get_text(strip=True)
            company = self._first_text(
                card,
                [
                    ".base-search-card__subtitle",
                    ".job-card-container__primary-description",
                ],
            )
            location = self._first_text(
                card,
                [
                    ".job-search-card__location",
                    ".job-card-container__metadata-item",
                ],
            )
            description = self._first_text(
                card,
                [
                    ".base-search-card__snippet",
                    ".job-card-container__metadata-item--bullet",
                ],
            ) or "LinkedIn job listing"

            if not title or not company:
                logger.debug(
                    "LinkedIn skipping fallback card job_id=%s missing=%s",
                    job_id,
                    "title" if not title else "company",
                )
                continue

            seen_ids.add(job_id)
            jobs.append(
                JobPosting(
                    id=job_id,
                    title=title.strip(),
                    company=company.strip(),
                    location=(location or "").strip(),
                    description=description.strip(),
                    url=url,
                    source=self.name,
                    metadata={"raw_id": job_id},
                )
            )
        if jobs:
            logger.info("LinkedIn parsed %s fallback jobs", len(jobs))
        if not jobs:
            logger.info("LinkedIn search yielded 0 jobs (keywords=%s, location=%s)", self.keywords, self.location)

        return jobs

    @staticmethod
    def _first_text(card: Tag | None, selectors: List[str]) -> str | None:
        if card is None:
            return None
        for selector in selectors:
            node = card.select_one(selector)
            if node:
                text = node.get_text(strip=True)
                if text:
                    return text
        return None

    @staticmethod
    def _extract_job_id(url: str, link: Tag) -> str | None:
        match = re.search(r"/jobs/view/(\d+)", url)
        if match:
            return match.group(1)
        for attr in ("data-id", "data-entity-urn", "data-job-id", "data-view-id"):
            if link.has_attr(attr):
                value = link[attr]
                if value:
                    return value.split(":")[-1]
        return None

    def search_jobs(self, profile: CandidateProfile, limit: int | None = None) -> List[JobPosting]:
        max_results = limit or self.limit
        jobs: List[JobPosting] = []
        start = 0
        seen_ids: set[str] = set()

        while len(jobs) < max_results:
            logger.info("LinkedIn fetch start=%s keywords=%s location=%s", start, self.keywords, self.location)
            try:
                html = self._fetch_page(start)
            except httpx.HTTPError as exc:
                logger.warning("LinkedIn fetch failed (start=%s): %s", start, exc)
                break
            batch = self._parse_jobs(html)
            if not batch:
                logger.info("LinkedIn returned no job cards for start=%s", start)
                break
            for job in batch:
                if job.id in seen_ids:
                    continue
                seen_ids.add(job.id)
                jobs.append(job)
                if len(jobs) >= max_results:
                    break
            start += len(batch)

        if not jobs:
            logger.info("LinkedIn search yielded 0 jobs (keywords=%s, location=%s)", self.keywords, self.location)

        return jobs

    def apply(self, job: JobPosting, profile: CandidateProfile) -> ApplicationResult:
        # LinkedIn applications are usually handled via Easy Apply forms which
        # require browser automation. We simply return a status message so the
        # workflow can mark the job as handed off.
        message = (
            "LinkedIn adapter cannot auto-apply; please use the provided URL "
            "to submit the application manually."
        )
        return ApplicationResult(job_id=job.id, applied=False, message=message)


registry.register("linkedin", LinkedInJobSource)
