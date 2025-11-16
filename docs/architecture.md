# JobApplier Architecture

## Goals
- Parse a structured representation of the candidate profile (CV + preferences).
- Continuously search multiple job sources (APIs, RSS feeds, scraped pages) using pluggable connectors.
- Rank and filter roles against profile fit rules defined in configuration.
- Notify the user for approval with concise job briefs.
- Upon approval, auto-fill applications on supported boards and track submission status.

## High-Level Flow
1. **Profile Loader** reads `profile.yaml` and normalizes skills, experience, locations, and salary expectations.
2. **Search Orchestrator** runs on a schedule, invoking each job-source adapter with the normalized profile as a query.
3. **Deduplication + Scoring** merges search results, removes duplicates, then scores each job using heuristics/LLM relevance checks.
4. **Notifier** sends summaries (CLI, email, Slack, etc.) and waits for an approval signal.
5. **Application Executor** uses the relevant adapter to submit the application, logs the result, and updates tracking state.

## Key Modules
| Module | Responsibility |
| --- | --- |
| `config.py` | Load and validate app configuration (API keys, schedules, notification channels). |
| `profile.py` | Normalize CV/profile data and expose helper queries (e.g., canonical skill list). |
| `sources/base.py` | Define an abstract adapter interface (`search_jobs`, `apply`). |
| `sources/linkedin.py`, `sources/justjoin.py`, etc. | Implement source-specific scraping/API logic. |
| `scoring.py` | Score matches using rule-based weights or LLM evaluation. |
| `workflow.py` | Glue logic for search → approval → apply, orchestrated via a task queue or cron. |
| `notifiers/email.py`, `notifiers/slack.py` | Channel-specific approval requests. |
| `storage.py` | Persist job history, approvals, and applications (SQLite or simple JSON). |

## Extensibility
- **Connectors:** Add new job boards by subclassing `JobSourceAdapter`.
- **Notifications:** Plug additional notifiers via a shared base class.
- **Approval UX:** Today CLI prompts; future work could expose a lightweight web dashboard or Telegram bot.

## Roadmap
1. MVP with CLI prompts, YAML profile, single job source stub.
2. Add persistent store and background scheduling (e.g., APScheduler).
3. Integrate external LLM for job-to-profile matching.
4. Implement auto-form-fill for specific sites leveraging playwright/selenium. 
