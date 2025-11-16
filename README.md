# JobApplier

AI agent that searches for roles matching your CV, asks for approval, and auto-applies on your behalf via pluggable job-board connectors.

## Current Capabilities
- YAML-based profile ingestion that normalizes skills, locations, and preferences.
- Declarative configuration for job sources, scoring weights, and notification channel.
- LinkedIn job-source adapter that scrapes public job-search pages (requires your own LinkedIn session cookie).
- Heuristic scoring/ordering of results plus CLI approval workflow.
- JSON state tracking to avoid re-surfacing the same job twice.

See `docs/architecture.md` for the high-level design and roadmap.

## Project Layout
- `src/jobapplier/` – core package (config, profile loader, scorers, storage, workflow).
- `src/jobapplier/sources/` – job-board adapters (`mock.py` included as an example).
- `src/jobapplier/notifiers/` – approval channels (currently CLI).
- `samples/` – example config/profile data wired to LinkedIn.
- `.jobapplier-state.json` – runtime state (ignored until the agent runs).

## Quickstart
1. Install dependencies (editable install recommended):
   ```bash
   pip install -e .
   ```
2. Adjust `samples/profile.yaml` to represent your CV (pre-filled with Dawid Krzoska's C++/5G profile as an example) and `samples/config.yaml` for job sources + approvals.
3. Run one agent cycle (LinkedIn by default):
   ```bash
   PYTHONPATH=src python -m jobapplier.cli run \
     --config samples/config.yaml \
     --profile samples/profile.yaml \
     [--verbose]
   ```
4. Approve jobs directly in the prompt (`y` to apply, `n`/`s` to skip). Approved roles trigger the selected adapter's `apply` routine.

## Extending
- **Add job sources:** create `src/jobapplier/sources/<name>.py`, implement `JobSourceAdapter`, and register it via `registry.register`.
- **Add notifiers:** create a class implementing `BaseNotifier` and wire it inside `build_notifier`.
- **Advanced matching:** swap the heuristic scorer in `scoring.py` for an LLM-powered evaluation or vector similarity pipeline.

### LinkedIn Adapter Notes
- Configure a LinkedIn source block in `config.yaml`:
  ```yaml
  job_sources:
    - type: linkedin
      options:
        keywords: "C++ telecom"
        location: "Poland"
        limit: 10
        remote: true
        session_cookie: "${LINKEDIN_LI_AT}"
  ```
- The adapter calls the public `seeMoreJobPostings` endpoint and parses listings with BeautifulSoup.
- Provide your `li_at` cookie via environment variable (or set it directly) to mimic an authenticated session; unauthenticated sessions return far fewer jobs.
- Use `--verbose` when running the CLI to print LinkedIn fetch/log messages (useful to confirm the HTTP request succeeds).
- Auto-applying on LinkedIn typically requires browser automation, so the adapter currently surfaces job links and defers submission to you.


## Next Ideas
- Background scheduling via APScheduler or serverless cron.
- Additional notifiers (Slack, email, Telegram).
- Adapter implementations for Lever, Greenhouse, Indeed, etc.
- Automated form filling using Playwright/Selenium with credential vault integration.
