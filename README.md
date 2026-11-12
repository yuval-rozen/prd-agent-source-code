# PRD → GitHub Issues Agent

A CLI agent that turns a PRD (PDF / DOCX / MD / TXT) into a validated GitHub issue tree
(Epic → User Stories → Technical Tasks) and publishes it idempotently. The full specification is in
[SPEC.md](SPEC.md).

> This README is being filled in milestone by milestone; the complete version lands in milestone 6.

## Setup

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/):

   macOS / Linux:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   Windows (PowerShell):

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. Install the dependencies (uv creates `.venv/` and picks a matching Python ≥ 3.11):

   ```bash
   uv sync
   ```

3. Configure secrets: copy `.env.example` to `.env` and fill in the values. `.env` is gitignored.

   | Variable | Required | Notes |
   |---|---|---|
   | `ANTHROPIC_API_KEY` | unless `--replay` | |
   | `GITHUB_TOKEN` | only with `--publish` | fine-grained, test repo only, Issues read/write, short expiry |
   | `GITHUB_REPO` | only with `--publish` | `owner/name`, or pass `--repo` |
   | `GENERATION_MODEL`, `CRITIC_MODEL` | no | default `claude-sonnet-5-5` / `claude-opus-5-5` |

4. Run:

   ```bash
   uv run main.py run "prd/PRD To-Do Management System (1).pdf"
   ```

   ```bash
   uv run pytest
   ```

## Design decisions & trade-offs

- **No sampling parameters; repeatability comes from the LLM cache.** Current Claude models reject
  `temperature` / `top_p` / `top_k`, so none are sent. Runs are made repeatable by the LLM response cache
  (`.cache/llm/`, keyed by hash of model, messages, tools and schema): a re-run with the same inputs
  returns byte-identical responses, and `--replay` runs the whole pipeline from it without an API key.
  Content-derived IDs, deterministic reconcile and Jinja rendering keep the remaining code paths
  deterministic.
- **Native structured outputs, never forced tool calls.** Current models reject forced `tool_choice`.
  Every generation call uses `with_structured_output(Model, method="json_schema")`, which sends the
  schema as `output_config.format`. The critic is `langchain.agents.create_agent` (the successor of
  LangGraph's deprecated `create_react_agent`, whose `response_format` falls back to forced tool calls)
  with `response_format=ProviderStrategy(ReviewReport)`, so its final report is also native structured
  output while its PRD lookup tools stay ordinary, unforced tools.
- **Schema rules vs. review rules.** Pydantic enforces only rules local to one field (key formats,
  non-empty Given/When/Then, unique labels, non-empty titles). Anything the repair loop should be able
  to fix — including the 80-character title limit (P11) — is a validator finding, so one bad title is
  repaired instead of failing the whole structured response.
