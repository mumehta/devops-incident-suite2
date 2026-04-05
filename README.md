# DevOps Incident Analysis Suite

A multi-agent AI application that automates DevOps incident review from raw log files. Upload or paste ops logs and a 5-agent pipeline — orchestrated by LangGraph and powered by Claude Sonnet 4.5 — classifies incidents, generates remediation plans, sends Slack alerts, creates incident runbooks, and opens JIRA tickets automatically.

---

## Architecture Overview

```
Raw Logs (upload / paste)
        │
        ▼
┌──────────────────────────────────────────────────────┐
│              LangGraph Orchestrator                  │
│                                                      │
│  ┌─────────────┐    ┌─────────────┐                  │
│  │  Agent 1    │───▶│  Agent 2    │                  │
│  │ Log         │    │ Remediation │                  │
│  │ Classifier  │    │ Agent       │                  │
│  └─────────────┘    └──────┬──────┘                  │
│                            │                         │
│              ┌─────────────┼─────────────┐           │
│              ▼             ▼             ▼           │
│       ┌──────────┐ ┌────────────┐ ┌──────────┐      │
│       │ Agent 3  │ │  Agent 4   │ │ Agent 5  │      │
│       │ Slack    │ │ Cookbook   │ │  JIRA    │      │
│       │ Notifier │ │ Synthesizer│ │  Agent   │      │
│       └──────────┘ └────────────┘ └──────────┘      │
└──────────────────────────────────────────────────────┘
        │
        ▼
  Streamlit UI (port 8501) + FastAPI (port 8000)
```

### Agent Responsibilities

| # | Agent | File | What it does |
|---|-------|------|--------------|
| 1 | **Log Classifier** | `agents/log_classifier.py` | Parses raw logs with Claude; extracts issues with severity, affected service, and error pattern |
| 2 | **Remediation Agent** | `agents/remediation.py` | Generates root cause, immediate actions, step-by-step fix, bash commands, and prevention per issue |
| 3 | **Notification Agent** | `agents/notification.py` | Formats top issues as Slack Block Kit message and posts to your channel |
| 4 | **Cookbook Synthesizer** | `agents/cookbook.py` | Generates a 4-phase incident runbook (Detect → Contain → Resolve → Post-Incident) |
| 5 | **JIRA Ticket Agent** | `agents/jira_agent.py` | Creates one JIRA task per issue with full context, mapped priority, and remediation steps |

### Orchestration

`orchestrator/graph.py` uses **LangGraph `StateGraph`** to wire agents into a sequential pipeline. A shared `IncidentState` TypedDict is passed through each node — each agent reads the previous output and appends its own. Errors are captured per node without halting the rest of the pipeline.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Package manager | [uv](https://docs.astral.sh/uv/) |
| UI | [Streamlit](https://streamlit.io) |
| REST API | [FastAPI](https://fastapi.tiangolo.com) + [Uvicorn](https://www.uvicorn.org) |
| Orchestration | [LangGraph](https://langchain-ai.github.io/langgraph/) |
| AI Model | Claude Sonnet 4.5 via [Anthropic SDK](https://docs.anthropic.com) |
| Slack alerts | [slack_sdk](https://slack.dev/python-slack-sdk/) |
| JIRA tickets | [python-jira](https://jira.readthedocs.io/) |
| Config | python-dotenv |

---

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — fast Python package manager
- `make` (macOS/Linux built-in; on Windows use Git Bash or WSL)
- An [Anthropic API key](https://console.anthropic.com) (separate from claude.ai subscription)
- Slack app with `chat:write` scope installed to your workspace
- JIRA account with API token and a target project

### Install uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

---

## Quick Start

### 1. Clone and install

```bash
git clone <repo-url>
cd devops-incident-suite2

make install        # uv sync — creates .venv and installs all deps
```

uv automatically creates a `.venv` in the project root and installs everything from `uv.lock`. No manual `python -m venv` needed.

### 2. Configure environment

```bash
make env            # copies .env_example → .env (skips if .env exists)
```

Open `.env` and fill in your credentials:

```env
ANTHROPIC_API_KEY=sk-ant-...
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C0XXXXXXX
JIRA_SERVER=https://yourorg.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=ATATT...
JIRA_PROJECT_KEY=SCRUM
MOCK_MODE=false
```

> Set `MOCK_MODE=true` to run the full pipeline without making real Slack or JIRA API calls — useful for development and demos.

Verify all variables are set:

```bash
make check-env
```

### 3. Start the app

```bash
make run            # Streamlit UI on http://localhost:8501
make run-api        # FastAPI on http://localhost:8000
make run-all        # both concurrently
```

---

## Application Access

### Streamlit Web UI

| Endpoint | URL | Notes |
|----------|-----|-------|
| **Web UI** | `http://localhost:8501` | Main Streamlit interface |
| **Streamlit health** | `http://localhost:8501/_stcore/health` | Returns `ok` when server is running |
| **Custom port** | `make run APP_PORT=8080` | Override via `APP_PORT` variable |

### FastAPI REST API

| Endpoint | URL | Notes |
|----------|-----|-------|
| **Swagger UI** | `http://localhost:8000/docs` | Interactive API docs — try endpoints in browser |
| **ReDoc** | `http://localhost:8000/redoc` | Alternative API reference docs |
| **Health check** | `http://localhost:8000/health` | Returns `{"status":"ok","version":"1.0.0"}` |
| **Analyze (JSON)** | `POST http://localhost:8000/analyze` | Submit log text as JSON body |
| **Analyze (upload)** | `POST http://localhost:8000/analyze/upload` | Upload a `.log` / `.txt` file |
| **Custom port** | `make run-api API_PORT=9000` | Override via `API_PORT` variable |

---

## REST API Usage

### Start the API server

```bash
make run-api               # starts on http://localhost:8000
make run-api-mock          # starts with MOCK_MODE=true (no Slack/JIRA calls)
make run-all               # starts both Streamlit (8501) and FastAPI (8000)
```

### POST /analyze — submit log text

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "log_content": "2024-01-15 10:23:45 ERROR payment-service: DB timeout\n2024-01-15 10:23:46 CRITICAL api-gateway: 503 upstream failure"
  }'
```

### POST /analyze/upload — upload a log file

```bash
curl -X POST http://localhost:8000/analyze/upload \
  -F "file=@orchestrator/sample_logs/sample.log"
```

### Response shape

Both endpoints return the same JSON structure:

```json
{
  "classified_logs": { "summary": "...", "issues": [...], "affected_services": [...] },
  "remediation":     { "overall_recommendation": "...", "remediations": [...] },
  "notification":    { "status": "sent|mocked|error", "message": "...", "channel": "..." },
  "cookbook":        { "title": "...", "checklist": [...], "escalation_path": [...] },
  "jira_tickets":    { "status": "success|mocked|error", "tickets": [...], "total_created": 2 },
  "current_step":    "jira_tickets_created",
  "error":           null
}
```

### Try it in Swagger UI

1. `make run-api`
2. Open `http://localhost:8000/docs`
3. Click **POST /analyze** → **Try it out**
4. Paste log content into the request body and click **Execute**

---

## Running in Mock Mode

Mock mode runs the full 5-agent LangGraph pipeline using Claude for classification, remediation, and cookbook generation — but **skips the real Slack and JIRA API calls**, returning simulated responses instead.

```bash
make run-mock          # Streamlit UI in mock mode
make run-api-mock      # FastAPI server in mock mode
```

Recommended for development and demos when you don't have Slack/JIRA credentials configured.

---

## Project Structure

```
devops-incident-suite2/
├── app.py                          # Streamlit application entry point
├── server.py                       # FastAPI REST API entry point
├── pyproject.toml                  # Project metadata and dependencies (uv)
├── uv.lock                         # Locked dependency versions (commit this)
├── Makefile                        # Developer task automation
├── .env_example                    # Environment variable template
├── .env                            # Your local credentials (not committed)
│
├── agents/
│   ├── log_classifier.py           # Agent 1: log parsing and issue extraction
│   ├── remediation.py              # Agent 2: fix strategies and commands
│   ├── notification.py             # Agent 3: Slack Block Kit notification
│   ├── cookbook.py                 # Agent 4: incident runbook generation
│   └── jira_agent.py               # Agent 5: JIRA ticket creation
│
├── orchestrator/
│   ├── graph.py                    # LangGraph StateGraph pipeline definition
│   └── sample_logs/
│       └── sample.log              # Example multi-service incident log
│
└── utils/
    └── helpers.py                  # Environment variable loader
```

---

## Dependency Management with uv

Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`. Both files are committed to version control.

### Common uv operations

```bash
# Install / sync
make install                    # install runtime deps (uv sync)
make install-dev                # install runtime + dev deps (ruff, pytest)

# Add a new package
make add PKG=httpx              # adds to [project.dependencies]
make add-dev PKG=pytest-cov     # adds to [dependency-groups] dev

# Update lock file after editing pyproject.toml manually
make lock                       # uv lock (no install)

# Export to requirements.txt (for CI or tools that need it)
make export-requirements
```

> All runtime commands (`make run`, `make run-api`, `make test`, etc.) use `uv run` — they automatically use the managed `.venv` without you needing to activate it manually.

---

## Makefile Reference

```bash
make help
```

| Target | Description |
|--------|-------------|
| `make help` | Show all available targets with descriptions |
| **Setup** | |
| `make env` | Copy `.env_example` → `.env` (skips if `.env` exists) |
| `make install` | Install runtime dependencies via `uv sync` |
| `make install-dev` | Install runtime + dev dependencies (ruff, pytest) |
| `make lock` | Regenerate `uv.lock` from `pyproject.toml` without installing |
| `make add PKG=x` | Add a runtime dependency via `uv add` |
| `make add-dev PKG=x` | Add a dev-only dependency via `uv add --dev` |
| `make export-requirements` | Export lock file to `requirements.txt` for compatibility |
| **Run** | |
| `make run` | Start the Streamlit app on port 8501 |
| `make run-mock` | Start Streamlit with `MOCK_MODE=true` (no Slack/JIRA calls) |
| `make run-headless` | Start Streamlit without auto-opening a browser |
| `make run-api` | Start the FastAPI server on port 8000 with auto-reload |
| `make run-api-mock` | Start FastAPI with `MOCK_MODE=true` |
| `make run-all` | Start both Streamlit (8501) and FastAPI (8000) concurrently |
| **Quality** | |
| `make lint` | Lint all Python files with `ruff` |
| `make lint-fix` | Auto-fix lint issues with `ruff` |
| `make format` | Format all Python files with `ruff` formatter |
| `make test` | Run test suite with `pytest` |
| **Utilities** | |
| `make check-jira` | Query your JIRA project and print available issue types |
| `make check-env` | Verify all required environment variables are set |
| `make sample-run` | Run the pipeline against the bundled `sample.log` (CLI output) |
| **Cleanup** | |
| `make clean` | Remove `__pycache__` dirs and `.pyc` files |
| `make clean-all` | Remove cache, `.venv`, and `.env` (prompts for confirmation) |

### Overriding ports

```bash
make run APP_PORT=9000          # Streamlit on custom port
make run-api API_PORT=9000      # FastAPI on custom port
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | API key from [console.anthropic.com](https://console.anthropic.com) |
| `SLACK_BOT_TOKEN` | Yes | OAuth token for your Slack app (`xoxb-...`) |
| `SLACK_CHANNEL_ID` | Yes | Target channel ID (e.g., `C0XXXXXXX`) |
| `JIRA_SERVER` | Yes | Your JIRA base URL (e.g., `https://org.atlassian.net`) |
| `JIRA_EMAIL` | Yes | Email address linked to your JIRA account |
| `JIRA_API_TOKEN` | Yes | API token from [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens) |
| `JIRA_PROJECT_KEY` | Yes | JIRA project key where tickets will be created (e.g., `SCRUM`) |
| `MOCK_MODE` | No | Set to `true` to skip real Slack/JIRA API calls. Defaults to `false` |

---

## How to Use the App

1. Open `http://localhost:8501` in your browser
2. In the **Upload** tab, upload a `.log` or `.txt` file — or switch to **Paste Logs** and paste content directly
3. Click **Analyze Incident**
4. Watch the 5-agent pipeline execute with live status indicators
5. Review results per agent:
   - **Metrics dashboard** — total issues, critical/high counts, affected services
   - **Log Analysis** — structured issue table with severity and error patterns
   - **Remediation Plan** — prioritized fixes with commands
   - **Slack Notification** — preview of the message sent to your channel
   - **Incident Cookbook** — phased runbook with escalation path
   - **JIRA Tickets** — created ticket IDs with links
6. Use **Download Report** to export the full result as JSON

---

## Testing the Pipeline Without a Log File

```bash
make sample-run
```

Runs the entire LangGraph pipeline in CLI mode against the bundled `sample.log` and prints structured JSON output for all 5 agents. Good first check after configuring `.env`.

---

## Security Notes

- **Never commit `.env`** — it is listed in `.gitignore`. Use `.env_example` as the template.
- Rotate any credentials that have been accidentally committed to version history using [BFG Repo Cleaner](https://rtyley.github.io/bfg-repo-cleaner/).
- The Slack bot token needs only the `chat:write` scope.
- The JIRA API token is tied to your user account — use a service account token for production.
