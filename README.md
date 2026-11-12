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
   | `LLM_PROVIDER` | no | `anthropic` (default) or `google` |
   | `ANTHROPIC_API_KEY` | with `anthropic`, unless `--replay` | |
   | `GOOGLE_API_KEY` | with `google`, unless `--replay` | AI Studio key of a project **without billing** (free tier only) |
   | `MAX_PARALLEL_CALLS` | no | default 4 (anthropic) / 1 (google) |
   | `GITHUB_TOKEN` | only with `--publish` | fine-grained, test repo only, Issues read/write, short expiry |
   | `GITHUB_REPO` | only with `--publish` | `owner/name`, or pass `--repo` |
   | `EXTRACT_MODEL` | no | S2 extraction; default `claude-haiku-5-5` / `gemini-3.5-flash-lite` |
   | `GENERATION_MODEL` | no | S4 / S5 / S6 / repair; default `claude-sonnet-5-5` / `gemini-3.8-flash` |
   | `CRITIC_MODEL` | no | S7 critic; default `claude-sonnet-5-5` / `gemini-3.8-flash` |
   | `MAX_RUN_COST_USD` | no | hard cost cap per run, default `0.50` |
   | `EXTRACT_EFFORT`, `GENERATION_EFFORT`, `CRITIC_EFFORT` | no | reasoning effort, default `low` / `medium` / `medium` |

   During development all three models can be set to `claude-haiku-5-5`.

4. Run:

   ```bash
   uv run main.py run "prd/PRD To-Do Management System (1).pdf"
   ```

   ```bash
   uv run pytest
   ```

## Choosing a provider

`LLM_PROVIDER=anthropic` (default) or `google`. Both run the same pipeline, prompts, schemas and checks;
only the model client differs. Responses are cached per provider, so the two can be compared on the
same PRD by running into different output folders:

```bash
uv run main.py run "prd/PRD To-Do Management System (1).pdf" --out out/gemini
```

**Google free tier**

- Only Gemini models with a free tier are allowed (`gemini-3.8-flash`, `gemini-3.6-flash`,
  `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`); they are priced at $0 and the cost cap stays on.
  Models without a free tier (for example `gemini-4-*`, `gemini-3.1-pro-preview`) are refused. Nothing
  billable is enabled: no context caching, no grounding.
- Use an AI Studio key whose Google Cloud project has **no billing account**. The code cannot detect
  billing; on a billed project the same models are charged.
- **Free-tier prompts and responses may be used by Google to improve its products** (Google's pricing
  page lists "Used to improve our products: Yes" for the free tier). Do not send confidential PRDs.
- Limits are per project, not per key, and small. Google shows the exact numbers only in AI Studio;
  third-party reports put `gemini-3.8-flash` at about 5 requests/minute and 20 requests/day, and Flash-Lite
  at about 10/minute and 500/day. So calls run one at a time, a 429 is retried after the delay the API
  returns, and a per-day quota error stops the run with a clear message (quotas reset at midnight Pacific).
  A first run on the sample PRD needs about 10 Flash-Lite calls and 10 Flash calls; re-runs are served
  from the cache.
- Prompt caching and reasoning effort are Anthropic-only and are not sent to Google. Gemini's own
  thinking level can be set with `GOOGLE_THINKING_LEVEL` (generation and critic stages only).
- Every LLM request times out after 180 s. Gemini 503 / 504 / timeouts are retried twice (15 s, 45 s).

## Model selection

All runs below are milestone 2 runs (S1 → S2 → S4 → S5 → S8, no checks yet) on the sample PRD
(`prd/PRD To-Do Management System (1).pdf`, 45 units in 12 sections), from an empty LLM cache. Each run
writes `run_stats.json` next to its outputs.

### Runs

| | Run 1 — Gemini | Run 2 — Gemini | Run 3 — Claude |
|---|---|---|---|
| Date | 2026-11-12 | 2026-11-12 | 2026-11-12 |
| Provider | google (free tier) | google (free tier) | anthropic |
| S2 extract model | `gemini-3.5-flash-lite` | `gemini-3.5-flash-lite` | `claude-haiku-5-5` (effort low) |
| S4 / S5 generation model | `gemini-3.8-flash` (default thinking) | `gemini-3.8-flash` (thinking `low`) | `claude-haiku-5-5` (effort medium) |
| Critic model (M3, not used yet) | `gemini-3.8-flash` | `gemini-3.8-flash` | `claude-haiku-5-5` |
| Client | langchain-google-genai 3.2.0, 600 s timeout, no 5xx retry | langchain-google-genai 4.5.0, 180 s timeout, 2 retries on 503/504 | langchain-anthropic 1.7.10, 180 s timeout, SDK retries |
| Parallel calls | 1 | 1 | 4 |
| S1 load_prd | ~2 s | 1.5 s | 1.6 s |
| S2 extract_requirements | ~140 s | 170.8 s — **failed** | 8.5 s |
| S4 plan_stories | **failed** after ~13 min | not reached | 12.3 s |
| S5 detail_stories | not reached | not reached | 38.3 s |
| S8 render_preview | not reached | not reached | 0.1 s |
| Total (wall clock) | 907 s | 172 s (179 s wall) | 60.8 s (67 s wall) |
| Cost | $0.00 | $0.00 | $0.0201 (cap $0.10) |
| Successful API calls | 11 | 3 | 19 |
| Tokens | 10,668 in · 3,795 out | 2,796 in · 821 out | 76 uncached in · 24,067 cache read · 34,281 cache write · 31,066 out |
| Errors / timeouts | S4: `504 DeadlineExceeded` after one call hung ~13 min | S2: 3 × HTTP 503/504 (`GoogleAPIError`), gave up after 2 retries | none |
| Rate-limit (429) waits | 0 | 0 | 0 |
| Free-tier limits | Not published by Google outside AI Studio. Third-party reports: `gemini-3.8-flash` ≈ 5 RPM / 20 RPD, Flash-Lite ≈ 10 RPM / 500 RPD (per project) | same | not applicable (paid API; bounded by `MAX_RUN_COST_USD`) |
| Output | none (no plan.md) | none (no plan.md) | [`out/claude/plan.md`](out/claude/plan.md) |

### Objective quality indicators

Only run 3 produced a plan. The indicators are computed from `out/claude/plan.json` and
`out/claude/validation_report.md`; none of the M3 checks or the critic have run yet.

| Indicator | Run 1 — Gemini | Run 2 — Gemini | Run 3 — Claude |
|---|---|---|---|
| Requirements extracted (actionable / context only) | (S2 completed, plan not produced) | — | 41 (35 / 6) |
| PRD units covered by a requirement | — | — | 41 / 45: the four Frontend Requirements bullets "Task creation/editing form", "Status and Priority indicators", "Loading, Empty, and Error states", "List auto-refresh upon task changes" were not extracted |
| Stories / tasks | — | — | 7 / 33 (14 BE, 12 FE, 7 QA; 1 spike) |
| ACs per story (min / avg / max) | — | — | 4 / 6.1 / 7 |
| Actionable requirements cited by a ticket | — | — | 35 / 35 |
| Titles over 80 characters (P11) | — | — | 2 (`BE-tasks-table-migration` 92, `BE-delete-task-error-responses` 81) |
| Reference findings | — | — | 1 (`REF-UNIT`: a mangled unit ID for "Task list view." was re-attached) |

### Decision and rationale

<!-- To be filled in after reviewing the plans. -->

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
- **Hard cost control.** Each live call is priced from its response `usage` (uncached input, cache
  reads, cache writes, output) with the price table in `config.py`. A configured model without a price is
  refused, because the cap could not be enforced for it. No call starts once the run has spent
  `MAX_RUN_COST_USD`, and the run aborts (exit code 7) as soon as a response pushes it over. Up to four
  calls run in parallel, so the overshoot is bounded by the calls already in flight. Responses are cached
  before the check, so re-running after an abort resumes without paying twice. S11 prints the total.
- **Model and effort per stage.** Extraction is a narrow, per-section task, so it runs on Haiku at low
  effort; planning, detailing and critique run on Sonnet at medium effort. Thinking tokens are billed as
  output, so effort is the second cost lever after model choice.
- **Prompt caching on every call.** A breakpoint on the system prompt (shared by all calls of a stage)
  plus automatic top-level caching (the critic's growing tool loop, validation retries). Cache writes
  cost 1.25× input, so a call with no reuse is slightly more expensive; prefixes below the model's
  minimum cacheable length are silently not cached. The S11 cost line reports cache reads and writes, so
  the effect is visible per run.
- **Schema rules vs. review rules.** Pydantic enforces only rules local to one field (key formats,
  non-empty Given/When/Then, unique labels, non-empty titles). Anything the repair loop should be able
  to fix — including the 80-character title limit (P11) — is a validator finding, so one bad title is
  repaired instead of failing the whole structured response.
