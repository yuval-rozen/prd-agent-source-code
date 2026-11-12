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
   | `GENERATION_MODEL` | no | S4 / S5 / S6 / repair; default `claude-haiku-5-5` / `gemini-3.8-flash` |
   | `CRITIC_MODEL` | no | S7 critic; default `claude-sonnet-5-5` / `gemini-3.8-flash` |
   | `MAX_RUN_COST_USD` | no | hard cost cap per run, default `0.30` |
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

**Decision:** Claude Haiku 5.5 (`claude-haiku-5-5`) for extraction and generation, Claude Sonnet 5.5
(`claude-sonnet-5-5`) for the critic. These are the defaults in `config.py` and `.env.example`;
`LLM_PROVIDER=google` stays available but is not used.

**Rationale:**

- **Gemini's free tier cannot carry the pipeline.** It failed twice, both times on server timeouts:
  a 504 after one call hung for ~13 minutes (run 1), and three 503/504 errors in a row during extraction
  (run 2). Its per-project limits (reported at about 5 requests/minute and 20/day for `gemini-3.8-flash`)
  cannot support a full run with repair rounds, let alone a live demo.
- **Haiku is fast and cheap enough to generate.** It finished M2 in about 1 minute for $0.02 (run 3),
  with every actionable requirement cited.
- **A cheap model generates, a stronger model reviews.** Haiku's M2 plan had problems that only show up
  across stories (duplicate migrations and endpoints, a task duplicated in two stories, work assumed to
  live in another story). A per-story generator cannot see them, so the critic must see the whole PRD and
  the whole plan at once. That one call per round is where the stronger model pays for itself; it is
  about three quarters of the run's cost (see the M3 runs below).

### Milestone 3 runs (Haiku generation, Sonnet critic, $0.30 cap)

Same PRD, `claude-haiku-5-5` for S2 / S4 / S5 / S6 / repairs and `claude-sonnet-5-5` for the critic.
Runs 5 and 6 reuse cached responses for the stages whose prompts did not change. Each run stopped at G1
(no terminal attached); outputs are written before the gate.

| | Run 4 | Run 5 | Run 6 (+ run 7: G1 feedback → PASS, committed in [`out/m3/`](out/m3/)) |
|---|---|---|---|
| Change before the run | first M3 run | overlap findings route to every named task's story; Given/When/Then dedup | S4/S5: shared requirements split per story, one complete table; critic caches only the PRD; keep the best round |
| PRD units covered | 45 / 45 | 45 / 45 | 45 / 45 |
| Blocking findings per S7 round | 8 → 5 → 4 → 3 | 8 → 4 → 1 → 5 | 6 → 1 → 2 (round 2 kept) |
| Final status | NEEDS_REVIEW (3 blocking) | NEEDS_REVIEW (5 blocking) | NEEDS_REVIEW (1 blocking, explained) |
| Stories / tasks | 8 / 40 | 8 / 38 | 10 / 38 |
| Total time | 269.5 s | 126.3 s | 170.8 s |
| Cost (critic share) | $0.2864 ($0.2185, 4 calls) | $0.1887 ($0.1651, 3 calls) | $0.1741 ($0.1268, 3 calls) |

Run 6, time and cost per stage:

| Stage | Time | Calls | Cost | Model |
|---|---|---|---|---|
| S1 load_prd | 2.4 s | 0 | $0.0000 | — |
| S2 extract_requirements | 0.1 s | 0 (cached) | $0.0000 | `claude-haiku-5-5` |
| S3 check_requirements | 0.0 s | 0 | $0.0000 | code |
| S4 plan_stories | 18.2 s | 1 | $0.0026 | `claude-haiku-5-5` |
| S5 detail_stories | 54.1 s | 10 | $0.0228 | `claude-haiku-5-5` |
| S6 map_dependencies | 14.0 s | 1 | $0.0026 | `claude-haiku-5-5` |
| S7 check_plan (validators + **critic**) | 13.7 s | 3 | **$0.1268** | `claude-sonnet-5-5` |
| repair_plan (2 rounds) | 70.4 s | 8 | $0.0191 | `claude-haiku-5-5` |
| S8 render_preview | 0.2 s | 0 | $0.0000 | code |
| **Total** | **170.8 s** | **23** | **$0.1741** | |

S2 was served from the cache in run 6. Its first live run (run 4) took 8.6 s and $0.0032 for 11 calls.

Run 6 ended with one finding (CRIT-MISSING on `US-create-task`): the PRD lists Creation Date and Last
Updated Date as task fields but does not say who sets them. That is a product decision, so it was left to
the reviewer at G1 instead of being guessed. The reviewer answered with the feedback
"US-create-task: the backend sets Creation Date and Last Updated Date on create." (run 7, the committed
`out/m3/`): everything up to G1 was served from the cache, one repair and one critic call applied the
decision ($0.0389, 21 s), and the run ended **PASS**. Reviewer decisions are passed to the critic and to
every later repair as authoritative context, and feedback starts a fresh repair cycle, so the loop can
never restore an earlier round that lacks the decision.

## Publishing to GitHub

```bash
uv run main.py run "prd/PRD To-Do Management System (1).pdf" --publish --repo owner/name
```

- Needs `GITHUB_TOKEN` (fine-grained, the test repository only, Issues: read and write, short expiry) and
  the repository (`--repo` or `GITHUB_REPO`). Dry runs (no `--publish`) never need a token.
- After G1, S9 reads the repository (read-only) and computes the diff; G2 shows every create / update /
  close and asks for confirmation (`--yes` skips the question; a NEEDS_REVIEW plan is refused unless
  `--force`). S10 then creates the epic, the stories and the tasks (blockers first), patches the bodies
  with the real issue numbers ("Parent: #N", "Blocked by: #N", child checklists), and closes removed
  tickets with a comment. Issues are never deleted.
- **Native ticket tree:** S10 also links every story as a sub-issue of the epic and every task as a
  sub-issue of its story (REST sub-issues API; the token's Issues: read and write permission covers it),
  so GitHub shows the tree with progress on the epic and each story. Links that already exist are
  skipped, so a second run still makes 0 changes; sub-issues added by hand are left alone. The checklists
  in the bodies stay as a fallback.
- Every managed issue carries the `prd-agent` label and ends with
  `<!-- prd-agent:key=<KEY>;hash=<content_hash> -->`. The hash comes from the plan data, not from the
  rendered body, so a second run with the same plan sends no writes at all. Issues without the marker are
  never touched.
- Any GitHub error stops the run with a clear message (exit code 5); rate limits and 5xx are retried.
  Because publishing is idempotent, re-running resumes where it stopped.

**Sample publish** (the PASS plan in [`out/m3/`](out/m3/), 2026-11-12): the issues are in the test
repository [yuval-rozen/prd-agent-issues](https://github.com/yuval-rozen/prd-agent-issues/issues), with
the epic at [#1](https://github.com/yuval-rozen/prd-agent-issues/issues/1).

| Run | Diff found by S9 | Written | Time |
|---|---|---|---|
| First publish | create 49 | 49 issues created, 11 bodies relinked in pass 2, 9 labels created | 111 s in S10 |
| Second run, same PRD | unchanged 49 | nothing (0 writes) | — |
| Sub-issue upgrade, same 49 issues | unchanged 49, link 48 | 48 native sub-issue links (10 stories under the epic, 38 tasks under their stories); no issue writes | 99 s total |
| Run after the upgrade | unchanged 49, link 0 | nothing (0 writes) | — |

## Design decisions & trade-offs

- **No sampling parameters; repeatability comes from the LLM cache.** Current Claude models reject
  `temperature` / `top_p` / `top_k`, so none are sent. Runs are made repeatable by the LLM response cache
  (`.cache/llm/`, keyed by hash of model, messages, tools and schema): a re-run with the same inputs
  returns byte-identical responses, and `--replay` runs the whole pipeline from it without an API key.
  Content-derived IDs, deterministic reconcile and Jinja rendering keep the remaining code paths
  deterministic.
- **Native structured outputs, never forced tool calls.** Current models reject forced `tool_choice`.
  Every generation call uses `with_structured_output(Model, method="json_schema")`, which sends the
  schema as `output_config.format` (Gemini: `response_json_schema`).
- **The critic is one structured call, not an agent.** It receives the full PRD and the full plan in a
  compact form and returns a `ReviewReport`. A ReAct critic with PRD lookup tools would see the plan
  piece by piece and pay for every tool round trip; the problems worth a strong model are the ones that
  span stories (overlapping tasks, work assumed to be in another story), and those need the whole plan
  in view. The `prd_search` helpers stay as code (R1 uses `verify_quote`). In repair rounds the critic
  still gets the whole plan as context but reports only on the repaired items.
- **Hard cost control.** Each live call is priced from its response `usage` (uncached input, cache
  reads, cache writes, output) with the price table in `config.py`. A configured model without a price is
  refused, because the cap could not be enforced for it. No call starts once the run has spent
  `MAX_RUN_COST_USD`, and the run aborts (exit code 7) as soon as a response pushes it over. Up to four
  calls run in parallel, so the overshoot is bounded by the calls already in flight. Responses are cached
  before the check, so re-running after an abort resumes without paying twice. S11 prints the total.
- **Model and effort per stage: a cheap model generates, a stronger model reviews.** Extraction (low
  effort), planning, detailing, dependencies and repairs (medium) run on Haiku; the critic runs on Sonnet
  (medium). Thinking tokens are billed as output, so effort is the second cost lever after model choice.
- **The repair loop keeps the best round.** Regenerating a story can fix one finding and introduce
  another. When the loop stops on a round that is worse than an earlier one, the earlier plan is kept and
  the report says so.
- **Prompt caching on every call.** A breakpoint on the system prompt (shared by all calls of a stage)
  plus automatic top-level caching (validation retries). The critic is the exception to the automatic
  part: it marks the end of the PRD as its breakpoint and sends the plan, which changes every round, as
  ordinary input. Writing ~18k plan tokens to the cache at 1.25× per round, never to be read back, was
  the critic's largest avoidable cost. Cache writes
  cost 1.25× input, so a call with no reuse is slightly more expensive; prefixes below the model's
  minimum cacheable length are silently not cached. The S11 cost line reports cache reads and writes, so
  the effect is visible per run.
- **Schema rules vs. review rules.** Pydantic enforces only rules local to one field (key formats,
  non-empty Given/When/Then, unique labels, non-empty titles). Anything the repair loop should be able
  to fix — including the 80-character title limit (P11) — is a validator finding, so one bad title is
  repaired instead of failing the whole structured response.
