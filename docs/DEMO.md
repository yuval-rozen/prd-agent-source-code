# Demo walkthrough

This walkthrough publishes the committed sample run to a fresh issues repository, shows that a second
run changes nothing, and then applies the v2 PRD as an update. The main path replays the recorded LLM
responses and reviewer answers from `.cache/llm/`, so it needs no API key and costs $0. It produces
exactly the committed plans in [`out/sample-v1/`](../out/sample-v1/) and
[`out/sample-v2/`](../out/sample-v2/).

## 0. Prepare

1. **Create an empty issues repository**, for example `owner/prd-agent-demo-2`. One repository holds
   one product: the agent closes managed issues whose keys are not in the plan.
2. **Create a fine-grained GitHub token** with access to that repository only, the permission Issues:
   read and write, and a short expiry.
3. **Fill in `.env`** (copy it from `.env.example`):

   ```
   GITHUB_TOKEN=<the token>
   ANTHROPIC_API_KEY=<only needed for the fallbacks in section 5>
   MAX_RUN_COST_USD=1.00
   ```

   `MAX_RUN_COST_USD=1.00` matters only for a live fallback; the replay steps cost $0. Pass the
   repository with `--repo` in every command, so `GITHUB_REPO` can stay unset.
4. **Use a fresh output folder** such as `out/demo`. If it already has a `plan.json`, the first run
   becomes an update run. `out/` is not gitignored, so do not commit `out/demo`.

## 1. Publish v1

```bash
uv run main.py run "prd/PRD To-Do Management System (1).pdf" --out out/demo --replay --gate-answers out/sample-v1/gate_answers.json --publish --repo owner/prd-agent-demo-2
```

1. **S1–S8 run from the cache.** The console shows each stage. The first critic round reports 9 blocking
   findings, and after 3 repair rounds 3 remain, so the status is NEEDS_REVIEW.
2. **G1 four times.** Each time, the recorded reviewer answer is shown as "Recorded answer: …". Press
   Enter to accept it:
   - feedback on `US-view-task-list`: a single user and no sign-in;
   - feedback on `US-update-task`: keep the per-row edit action and the previous values after a failed
     update;
   - feedback on `US-update-task`: if the task cannot be loaded into the edit form, show an error and
     do not open the form;
   - approve. The status is now PASS.
3. **G2.** It shows `create 45 · update 0 · close 0 · sub-issue links 44 · unchanged 0` and the list of
   new issues. Type `confirm`.
4. **S10 publishes.** It creates 1 epic, 8 stories and 36 tasks, adds the labels and the 44 sub-issue
   links, and S11 prints the epic's URL. In the sample recording this took 176 s. Writes are spaced at
   least 1 s apart.

Show the result on GitHub:

- the epic with its 8 stories in the Sub-issues panel;
- a story with its tasks and the "Blocked by" lines;
- the labels;
- the hidden marker at the end of a body: `<!-- prd-agent:key=…;hash=… -->`.

## 2. Run it again: 0 changes

```bash
uv run main.py run "prd/PRD To-Do Management System (1).pdf" --out out/demo --replay --publish --repo owner/prd-agent-demo-2
```

1. **An update run.** `out/demo/plan.json` now exists, so this is an update run: the requirement diff
   is `0 added · 0 changed · 0 removed`, and every story is carried over.
2. **At G1, type `approve`.** G1 offers the first recorded answer of `out/demo/gate_answers.json`,
   which is a feedback; pressing Enter would apply it again.
3. **S9** reports `45 managed issue(s) found · create 0 · update 0 · close 0 · link 0 · unchanged 45`,
   and G2 says "Nothing to change on GitHub." Nothing is written.

## 3. Update with the modified PRD

[examples/todo_prd_v2.md](../examples/todo_prd_v2.md) makes three changes:

- it adds a requirement: task titles of at most 100 characters;
- it changes one: sorting by Title as well;
- it removes one: reverting a Completed task to Open.

```bash
uv run main.py run examples/todo_prd_v2.md --out out/demo --replay --gate-answers out/sample-v2/gate_answers.json --publish --repo owner/prd-agent-demo-2
```

1. **The diff and the carry-over.** The requirement diff is `1 added · 1 changed · 1 removed`. 3 stories
   are carried over unchanged, and 5 are affected. Of the 36 tasks, 28 are unchanged.
2. **G1 twice.** The critic's 3 blocking findings are repaired before the first G1, so the status is
   already PASS. The recorded decision restores the date rules that the story regeneration dropped (see
   Known gaps in the README). Press Enter at each:
   - feedback on `US-update-task` and `US-create-task`: the backend sets the Last Updated Date on every
     save, and both dates on create;
   - approve.
3. **G2** shows `create 0 · update 15 · close 0 · sub-issue links 0 · unchanged 30`. Each update has its
   cause, for example `R-0b1853d6 added; G1 reviewer decision`, and the churn count is 0. Type
   `confirm`.
4. **S10** updates the 15 issues and creates, closes or relinks nothing.

Show the result on GitHub: an updated issue's history (for example the update story) and an untouched
issue from a carried-over story.

## 4. Run it again: 0 changes

```bash
uv run main.py run examples/todo_prd_v2.md --out out/demo --replay --publish --repo owner/prd-agent-demo-2
```

At G1, type `approve`. S9 reports `unchanged 45`, and nothing is written.

## 5. Fallbacks

- **Without `--replay`.** Drop `--replay` (and `--gate-answers`) from a command, and the run needs
  `ANTHROPIC_API_KEY`.
  - Requests that match the cache are still served from `.cache/llm/` for free; the rest go to the
    API, within `MAX_RUN_COST_USD`.
  - G1 offers no recorded answers. Type them: choose `feedback`, then paste one line from the
    recording's `gate_answers.json`, once for each line, then `approve`.
  - A fully live run (with `.cache/llm/` moved aside) gives a different plan from the recording. The
    sample recordings cost $0.60 for v1 and $0.45 for v2.
- **`--force`.** If a live run ends NEEDS_REVIEW, G2 refuses to publish. `--force` publishes anyway.
  Use it only after reviewing the remaining findings in `validation_report.md`.
- **A GitHub error** (exit code 5) stops the run with a clear message. Publishing is idempotent, so
  run the same command again to resume.
- **A cache miss under `--replay`** (exit code 4) means a request changed: the PRD file, a prompt, a
  schema or a model. Run without `--replay` to fill the cache.
