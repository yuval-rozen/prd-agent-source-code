# Design decisions and lessons

This document explains why the agent looks the way it does. Each section follows one problem: what
happened, why, what changed, the result, and the lesson. The current behavior is described in the
[README](../README.md) and specified in [SPEC.md](../SPEC.md). Numbers come from the recorded runs and
the commit history.

## 1. Model selection

**Problem.** The pipeline makes many narrow structured calls, plus one large review call per round. The
models had to be fast, cheap, reliable under load, and good enough to find cross-story problems.

**What was measured.** Three milestone-2 runs (S1 → S2 → S4 → S5 → S8, no checks yet) on the sample
PRD from an empty cache:

| | Gemini run 1 | Gemini run 2 | Claude run 3 |
|---|---|---|---|
| Models | `gemini-3.5-flash-lite` / `gemini-3.8-flash` (free tier) | same, thinking `low` | `claude-haiku-5-5` |
| Result | failed in S4: `504 DeadlineExceeded` after one call hung about 13 minutes | failed in S2: 3 × HTTP 503/504, gave up after 2 retries | full plan: 7 stories, 33 tasks |
| Time | 907 s | 172 s | 60.8 s |
| Cost | $0 | $0 | $0.0201 (19 calls) |

Haiku cited all 35 actionable requirements it extracted. It missed four frontend bullets, which led to
the R2 rule that a list item covered only as context_only is a finding.

**Decision.** Haiku generates and Sonnet reviews.

- Haiku's plans had problems that only show up across stories: duplicate migrations and endpoints, and
  stories that assumed another story built their part. Per-story generation cannot see those, so the
  critic sees everything at once on the stronger model.
- In the milestone-3 runs the Sonnet critic was most of the cost: $0.2185 of $0.2864, then $0.1268 of
  $0.1741.

**Update-run revisions.**

- With Haiku writing them, blocking findings went 3 → 4 → 4 → 6 on the v2 PRD, and the loop never
  converged.
- A separate `REVISION_MODEL` put only those calls on Sonnet. Blocking findings then went 3 → 3, then
  3 → 2 → 2, at about $0.03 per call (11 calls, $0.32).

**Result.** The current defaults are Haiku for extract and generation, and Sonnet for revision and the
critic. Gemini stays as an optional free-tier provider behind the same cache, cost and retry layer.
Opus and Fable were not needed.

**Lesson.** Spend the strong model where the whole context matters (review and targeted edits), and let
the cheap model do the many narrow calls. A free tier with small per-project limits and server timeouts
cannot carry a pipeline with repair rounds.

## 2. Critic evolution

**Step 1: a ReAct critic with tools (planned, then replaced).**

- *Design.* The first SPEC had the critic as an agent (`create_agent` with a structured response
  format) that looked things up through the `prd_search` tools.
- *Problem.* It would see the plan piece by piece and pay for every tool round trip, while the problems
  worth a strong model span stories. Getting structured output from an agent loop on both providers was
  a further complication.
- *Fix (milestone 3).* One structured call (`ReviewReport`) over the full PRD and a compact form of the
  plan. `prd_search` stayed as code helpers (R1 uses `verify_quote`), and the LLM has no tools at all.

**Step 2: from a compact plan to the whole plan.**

- *Problem.* The compact form left out fields such as task descriptions and DoD lines, and that is
  where unrequested scope was hiding. In the earlier v1 sample, phrases like "signed-in user" and "main
  navigation" got through.
- *Fix.* The critic now sees every story field and every task field. Each requirement's text appears
  once, in the requirement list, and is referred to by ID elsewhere.
- *Measurement.* In a read-only probe on the same plan, a critic call cost $0.061 before and $0.076
  after. The new critic flagged "signed-in user", "registered user" and "main navigation" as blocking
  `CRIT-UNREQUESTED`.

**Step 3: what may block.**

- *Problem.* A strict critic blocked on everything, including details the PRD simply does not settle
  (who sets a date, a default value). Those cannot be fixed by repair; they need a product decision.
- *Fixes.*
  - `CRIT-PRD-GAP` became a warning whose open question code adds to the story.
  - Blocking is limited to adding scope, contradicting the PRD, leaving a requirement or constraint
    uncovered, duplicate work, and ACs that cannot be verified. Code enforces this whatever severity
    the model returns.
  - Demoting `CRIT-OVERLAP` and `CRIT-UNTESTABLE-AC` to warnings was tried and reverted: the
    assignment requires no duplicate work and testable ACs.
  - The last change narrowed `CRIT-UNREQUESTED` to new scope (a feature, screen, field, user role,
    sign-in or permission), not test values or implementation details inside ACs. It also stopped
    reporting a gap the story already lists as an open question as `CRIT-MISSING`.
- *Result.* Fresh v1 recordings from an empty cache:

| Critic version | Blocking at G1 | Cost to G1 |
|---|---|---|
| Whole plan; PRD gaps as warnings; overlap and untestable ACs blocking | 11 | $0.2757 (39 calls) |
| Plus the narrowed UNREQUESTED and open-question rules | 3 | $0.3133 (42 calls) |

The 3 remaining findings were real: "signed-in user" in the list story, the per-row edit action, and a
missing error case for loading a task into the edit form. Three G1 decisions settled them.

**Lesson.** A reviewer is only useful if its blocking findings are ones a repair can fix. Things the
PRD leaves open belong to a human, as open questions, not in the repair loop.

## 3. The G1 feedback bugs

**Problem.** In milestone 3, the reviewer's G1 answer ("the backend sets Creation Date and Last Updated
Date on create") did not stick, for two reasons:

- After the repair, keep-best compared rounds and could restore an earlier plan, one that did not yet
  contain the decision.
- The critic saw the decision's effect in the plan, with no PRD sentence behind it, and could report it
  as unrequested.

**Cause.** The decision was treated like any other repair input. Nothing marked it as authoritative,
and nothing stopped the loop from restoring a plan without it.

**Fix.** Feedback is a reviewer decision:

- It stays in the state, and from milestone 5 on it is persisted in `plan.json`.
- It is given to the critic and to every later repair as authoritative context, treated like PRD text.
- It starts a fresh repair cycle: the round count, the blocking history and the best-round baseline are
  reset, so a round without the decision can never be restored over it.

**Result.** The milestone-3 sample reached PASS with one repair and one critic call ($0.0389, 21 s).

**Lesson.** Human input must be stronger than the machinery's own memory. Any "keep the best version"
logic has to be reset when the human changes the target.

## 4. The update-run carry-over bug

**Problem.** The first v2 update run carried over no story at all, and G2 would have updated 48 of the
49 published issues for three small requirement changes.

**Cause.** S4 re-planned the whole plan, and it re-scoped the cross-cutting constraint "no optimistic
UI" from 5 requirements to global. Every story then had a changed constraint set, so every story looked
affected.

**Fix.** The update is stabilized by code. Unchanged requirements keep their previous story and
constraint scope, a changed requirement takes its old version's place, and S4 decides only where
added requirements go.

**Result.** The diff fell from 48 updates to 20 (create 3, update 20, close 4, link 3, unchanged 25),
with 5 stories carried over.

**Lesson.** In an update, the LLM should decide only what the change requires. Everything else has to
be pinned by code, or the model's freedom to rephrase turns into noise on GitHub.

## 5. Task-level churn

**Problem.** Even with stories carried over, the affected stories were regenerated with all their
tasks. In the v2 diff, issue #40 (`QA-task-update-tests`) was to be closed and recreated as
`QA-task-update-test-suite`: the same test suite under a new key.

**Cause.**

- Task keys came from the regenerated output.
- Nothing required a changed task to have a reason to change.

**Fix.**

- **Classification.** Code sorts every task of an affected story:
  - KEEP: it cites no changed or removed requirement, so it is copied byte-for-byte.
  - REVISE: it cites one, so it is revised, keeping its key, story, track and blockers.
  - CLOSE: all of its requirements were removed.
- **The LLM's part.** It returns only the REVISE tasks and one placement for each added requirement.
- **Key reuse.** An old key is reused only for the same story and track with shared requirements.
- **Churn guard.** Any change without a requirement cause, G1 decision or repaired finding is restored
  by code.
- **Causes at G2.** G2 shows the cause of every action and counts churn.

**Result.** The v2 diff went from create 3 / update 20 / close 4 to create 0 / update 15 / close 0,
with churn 0. The fresh v2 recording on the new repository also published 15 updates with churn 0.

**Lesson.** Stable identity has to be decided by code from data (story, track, requirements), never
taken from text the model regenerates.

## 6. Repair whack-a-mole, story-wide decisions and the open-findings ledger

**Problem.**

- **Whack-a-mole.** Repairs fixed one finding and created another.
- **Lost findings.** Findings disappeared without being fixed: rounds 2–3 review only the repaired
  items, and a G1 reset started a fresh cycle.
- **Sibling tasks.** A G1 decision that named only a story let the model revise a minimal set of its
  tasks, which left sibling tasks inconsistent. In one v2 retry, the decision "the status endpoint only
  marks a task as Completed" was applied to the endpoint task, while the story's AC and the
  error-handling task still accepted Open. The retry stopped at its $0.50 cap with 2 blocking findings.

**Cause.**

- Findings were facts of one round, not tracked items.
- A story-level decision was treated as a minimal edit.

**Fix.**

- **The open-findings ledger.** Every blocking critic finding gets an ID and stays open across rounds,
  keep-best restores and G1 resets. The critic receives the open findings and must put each one in
  `resolved` or `still_open`; one it does not mention stays open.
- **Story-wide decisions.** A decision that names a story revises its ACs and every task that conflicts
  with it.
- **Plan-wide decisions.** A decision without a key is checked by the critic against the whole plan.

**Result.** The v2 update then reached PASS. For one plan-wide decision, the critic found 10 conflicts
and one repair fixed them all. It was published as 15 updates, and a second run made 0 changes.

**Lesson.** A loop of an LLM generator and an LLM reviewer needs memory outside both. A finding is closed
when the reviewer confirms it is fixed, not when it stops being mentioned.

## 7. Internal notes in tickets, and field-level repairs

**Problem.** Ticket text started to contain the agent's own bookkeeping: requirement IDs, ticket keys,
"reviewer decision", "the PRD text for this story". This is noise for the people who read the issues.

**Fix, part 1.** A plain-language rule in the story prompts, and a blocking check, P12.

**Problem with that fix.** P12 was first repaired by regenerating the story, and the regeneration
dropped lines nobody had asked to change. Examples are "Last Updated Date is set on every successful
update" in #4, "accepts only Completed" in #6, and an edge case from an earlier G1 decision.

**Fix, part 2.** Every repair became field- or line-level:

- **P12.** One small call rewrites only the flagged texts, and names the notes to remove in each, with
  one retry. Code puts each text back in its place and moves any named requirement ID into
  `requirement_ids`.
- **Story and task repairs** return numbered edits: replace, add or remove an AC, an edge case or DoD
  line n, or give a new description. Code applies them and keeps every other line byte-for-byte.
- **The epic** has its own small repair call.

**Result.** The v2 follow-up changed exactly four issues (#4, #6, #18, #42), each only in the flagged
lines, and a second run made 0 changes.

**Lesson.** Let the model return a diff, not a document. Code can then guarantee that nothing else
moves. One place still regenerates whole stories: the first pass over an affected story in an update
run. It is listed as a known gap in the README.

## 8. Human-closed issues versus agent-closed issues

**Problem.** The agent closes issues whose tickets left the plan, and reopens a closed issue whose key
comes back. A person may also close a managed issue, for example as completed, and reopening it would
undo their decision.

**Fix.**

- When the agent closes an issue, it adds `;closed=agent` to the marker.
- Only issues with that mark are ever reopened.
- An issue a human closed is never reopened, updated or re-linked, and S9 reports it as left closed.

**Lesson.** When a tool shares a system of record with people, it should only undo its own actions.

## 9. Why the design is more complex than one LLM call

A single prompt could turn a PRD into issues. Each mechanism here exists because of a specific way an
LLM fails:

| LLM risk | Mechanism |
|---|---|
| Invents requirements or quotes | verbatim `source_quote` per requirement, fuzzy-grounded in the PRD (R1) |
| Skips parts of the PRD | atomic units and unit coverage (R2), requirement coverage (P1) |
| Unstable IDs across runs | content-derived requirement IDs, code-assigned ticket keys, key reconcile |
| Invalid or partial output | native JSON-schema structured output, Pydantic models, one retry with the error |
| Malformed ticket structure | deterministic checks P2–P13, repaired item by item |
| Misses problems across stories | one critic call over the whole PRD and the whole plan, on a stronger model |
| A reviewer that never converges | blocking limited to fixable defects, PRD gaps as open questions, stop conditions, keep-best, the open-findings ledger |
| A repair breaks what was right | line-level edit schemas; code keeps every other line byte-for-byte |
| Noise in an update | carry-over, KEEP / REVISE / CLOSE, the churn guard, a cause for every change at G2 |
| Overwrites a human decision | G1 decisions as authoritative context, a fresh repair cycle, `closed=agent` |
| Writes the wrong thing to GitHub | no LLM tools; code writes only after G1 and G2; marker and hash idempotency |
| Runaway cost | a price per model, a hard per-run cap, and a response cache written before the budget check |
| Non-reproducible results | the response cache and `--replay` with recorded G1 answers, tested end to end |

## 10. Scope and possible extensions

**One product per issues repository.** The marker holds the ticket key and content hash. The listing
manages every issue with the `prd-agent` label and a marker, and a key that is missing from the plan is
closed. Two products in one repository would therefore close each other's issues.

**Possible extensions:**

- **Several products per repository:** a product ID in the marker and label.
- **Fewer reworded lines in update runs:** line-level updates for affected stories in their first pass,
  as repairs already do.
- **Content hash:** include the template version, so a template change refreshes existing bodies.
- **Manual edits:** reconcile edits made in GitHub instead of overwriting them when the PRD changes a
  ticket.
- **Other trackers** (for example Jira): behind the same sync-diff interface.

## 11. Mechanics in detail

These are the rules behind the README's short descriptions. [SPEC.md](../SPEC.md) states them
normatively.

**The critic's input and output**

- **Input:** the full PRD, then the whole plan:
  - the epic, with its scope, goals and their citations;
  - every story field: requirements, dependencies, the user story sentence, business description and
    value, ACs, edge cases, DoD;
  - every task field: track, area, size, flags, derived reason, requirements, `blocked_by`, the full
    description, DoD.

  Each requirement's text appears once, in the requirement list at the end, and is referred to by ID
  everywhere else.
- **Unknown values:** a check ID outside the list becomes `CRIT-OTHER`, and an item key that does not
  exist is cleared.
- **Open questions from PRD gaps:**
  - The critic writes the question in plain product language, and code appends it to the story's edge
    cases. For a task, it goes to the task's story.
  - A question the story already lists (near-identical wording, ignoring case and punctuation) is not
    added again.
  - The questions are kept across rounds, keep-best restores and G1 resets.

**The repair loop**

- **Scope of review:** rounds 2–3 of the critic review only the repaired items, with the whole plan as
  context. Their findings on other items are discarded, and earlier findings on unrepaired items are
  carried over. The validators run on the whole plan every round.
- **Routing:**
  - A finding on a story or task repairs that story.
  - `CRIT-OVERLAP` also repairs every story whose task it names.
  - A finding with only requirement IDs (P1, for example) adds the requirement to the story that cites
    most requirements of the same PRD section.
- **Stop conditions:** `MAX_REPAIR_ROUNDS` (3), no decrease in the blocking count, or no blocking
  finding that can be tied to a story or task. If the last round is worse, the plan of the round with
  the fewest blocking findings is kept, and `validation_report.md` says so.
- **The open-findings ledger:**
  - Each blocking critic finding gets an ID, and every critic call receives the open findings.
  - The critic must put each ID in `resolved` or `still_open`; one it does not mention stays open.
  - A keep-best restore brings back that round's open findings, and findings raised later stay open.
- **Narrow repairs:**
  - **P12:** one call rewrites only the flagged texts, with one retry for a text that still contains a
    note.
  - **The epic:** findings on the epic are fixed by one `EpicRepairDraft` call that returns the
    citations of the scope and of each numbered goal; it never removes the last goal.
  - **Stories and tasks:** repairs return numbered edits, and an edit with an unknown line number is
    ignored and logged.
- **Citations from findings and decisions:** when a repair addresses a finding or decision that names
  an existing requirement (by ID, in `requirement_ids`, or by a near-verbatim quote of 4+ words), code
  adds that ID to the story and to the tasks revised for it. The model never adds IDs.

**The gates**

- **G1 answers:** approve, feedback or abort.
  - A decision with ticket keys targets those items.
  - A decision without a key is reviewed by the critic against the whole plan, and the conflicts it
    finds are repaired like other findings.
  - Feedback resets the round count, the blocking history and the best-round baseline.
- **`gate_answers.json`** holds the sha256 of the PRD file, the G1 answers in order (with the feedback
  text) and the G2 answers. A replay offers the i-th G1 answer at the i-th G1, and only for the same
  PRD file. End of input never accepts a recording; it aborts.

**The update flow**

- **Requirement diff:** a removed requirement and an added one whose normalized quotes fuzzy-match
  (≥ 85) are reported as one changed requirement.
- **Keys:** S4 gets the previous plan as an anchor, and a deterministic reconcile maps a new story key
  to an old one when requirement overlap and title similarity pass a threshold. If `plan.json` is
  missing, the anchor is rebuilt from the existing issues' keys and titles.
- **Stories:** a story is unchanged when its requirements and its applicable constraints are unchanged,
  and an unchanged story is carried over byte-for-byte. The epic keeps its key and text; its citations
  follow the diff.
- **Tasks:** KEEP / REVISE / CLOSE and the churn guard are described in §5. In S6, only new tasks get
  blockers. The critic's first round reviews only items that differ from the previous plan, and
  nothing at all if none differ.

**Caching and cost control**

- **The prompt-caching measurement:** the critic used to send the plan inside the cached prefix. Each
  call wrote about 18k plan tokens to the cache, at 1.25× the input price, and they were never read
  back, because the plan changes every round. Now the critic's breakpoint sits at the end of the PRD,
  and the plan is ordinary input.
- **Prompt caching elsewhere:** every other call has a breakpoint on its system prompt, which all calls
  of a stage share, plus top-level automatic caching.
- **Cost:**
  - Each live call is priced from its response usage (uncached input, cache reads, cache writes,
    output) using the price table in `config.py`.
  - No call starts once the run has spent `MAX_RUN_COST_USD`, and a response that pushes the total over
    the cap stops the run.
  - Up to four calls run in parallel, so the overshoot is bounded by the calls in flight.
