# Issue pipeline

A set of Claude Code agents that take a tt-exalens change from a rough description to a reviewed local branch with a pull request description. Nothing is published: the agents never push and never write to GitHub. No agent touches a device; only the orchestrator runs tests, on machines you have reserved. You approve the issue, the design and the result, and you publish. If you switch a case to auto mode, the script takes those approvals for you.

## Using it

Start a new Claude Code session in the repository, so that the agent files are loaded. Then:

| Command | What it does |
|---|---|
| `/new-issue <description, issue link or file>` | Shapes a short issue with you and stops at Gate 0. An issue given by link is triaged first |
| `/resolve-issue <case>` | Investigates, designs (Gate A), writes tests, implements, reviews once, runs the tests on your reserved hardware, reports (Gate B) |
| `/fix-ci <case> <log file>` | Another round after you pushed and CI failed |
| `/papa [case ...]` | Proposes changes to the agent files from closed cases (Gate C) |

At a gate the session shows a document and its hash and waits. You edit the file or give feedback, and you approve with `approve <hash>`. If you edit the file, the hash changes, so an approval always names the version you read.

`.claude/pipeline/run status` lists the cases. `.claude/pipeline/run status <case>` shows where one stands and what comes next. `/resolve-issue --resume <case>` continues after an interruption.

## What you read

The documents written for you are short, and the script refuses them over their limits (`limits` in `config.json`).

| Document | Gate | What it says | Limit |
|---|---|---|---|
| `issue.md` | 0 | The problem and what done looks like, with at most five acceptance criteria | 250 words |
| `design.md` | A | What the change achieves, the API it changes, the modules and classes it adds, the sources of the hardware facts it changes | 300 words, not counting "Hardware facts" |
| `report.md` | B | What changed, how it was verified, what the review found | 400 words |
| `pr-description.md` | | Your pull request text, with the issue and the design folded in | |

The working detail is in files you do not have to read: `issue.notes.md` (findings, hints, open questions) and `plan.md` (files, steps, test spec). The approval of the design also covers the plan as it stood at that moment: neither can change afterwards without a new Gate A.

## The result: a local branch

The work lands on a local branch `<user>/<name>` in your repository.

- `<user>` is the part of your git e-mail address before the `@`, or `branch_user` in `config.json`.
- `<name>` is the name you give (`/new-issue ... on branch <name>`, or the `Branch:` line of the issue). Without one, the shaper makes a name from the issue. A number is added if the name is taken.

The branch holds the code and, under `docs/agentic/<name>/`, the approved `issue.md`, the approved `design.md` and `pr-description.md`. Set `branch_docs` in `config.json` to another directory, or to `""` to keep those three out of the branch.

Agents work in a separate clone, never in your working tree. After every commit the script updates the branch in your repository with `git fetch`, which moves only that branch. If you have the branch checked out, or changed your copy, it leaves your copy alone and `status` prints the command to take the commits yourself. Nothing is pushed: `git push -u origin <branch>` is yours to run, and the first line of `pr-description.md` is the pull request title.

## Review

There is one review round per iteration: implementation, review, then the comments are addressed once by the test writer and the implementer. The report lists each finding as fixed, not changed and why, or still open. For another round, say "review again" at Gate B. The orchestrator never starts one on its own (`caps.review` in `config.json`).

## Hardware runs

After the review round, the orchestrator runs the case's tests on your reservations with `.claude/pipeline/run hw-test <case>`. `.claude/pipeline/run hw-list` shows what it would use.

- **Machines.** `ird list` and `ird list-machines`, through `ssh yyz-ird` (`hardware.ird_host`), give your reservations and their architectures. It takes one Wormhole and one Blackhole reservation. When the change touches Quasar, it also takes the tensix reservation this session runs on. A change touches Quasar when a changed path or an added line names Quasar or Rocket, or when the plan lists `quasar`. Quasar runs on the emulator, or on the simulator when the emulator cannot run: no build, no answer from the submit host, or no connection within 15 minutes.
- **Tests.** The plan's `Hardware tests:` line, otherwise the device test modules the branch changes, with NOC0 and NOC1 on boards and NOC0 on Quasar.
- **Commands.** CLI commands get no unit tests. For each command the branch changes (or the plan's `Hardware commands:` line names), the Wormhole run starts the app with every example in the command's docstring, through the docs generator as `make docs` does, and checks that each example produced output in the generated section.
- **Missing reservations.** A target without a reservation (or a tensix reservation on another host) is noted in the report line and skipped. Nobody is asked, in either mode.
- **Boards.** It sends the committed branch over ssh as a git bundle. It builds it in `/localdev/<user>/issue-pipeline` on the machine, with a venv of its own there.
- **Quasar.** It builds in `.issue-pipeline/hardware/local/` and uses the builds under `hardware.quasar.simulators`.
- **Safety.** It does not use a board that any process holds. It stops a hung test and resets the board with `tt-smi -r`, only when nothing holds it. It runs one emulator or simulator at a time: if one of yours is running, it waits 10 minutes, then gives up. It never reserves, extends or releases a machine, and never restarts a host.
- **Results.**
  - Logs and failure excerpts go to `hardware/` in the case. The last lines are a `**Hardware:**` line for the report, without machine names.
  - Failing tests go back to the implementer.
  - The case keeps the latest result of each target, with the commit it tested. A run that a role asks for, with other tests, does not count.
  - When a reserved machine cannot be used (busy, unreachable, the build failed there, the board hung), a guided run asks you to free or fix it; auto mode records it as an accepted failure.
  - `advance report_ready` wants every target the case needs run on the current commit, or noted as not reserved. In guided mode you can go on without a target: `hw-test <case> --target <target> --skip "<reason>"`, or without `--target` for all of them.

Up to 4 runs per iteration (`caps.hw_runs`). `--dry-run` finds and checks the machines without building. `--build-only` ships and builds without running tests. The settings are under `hardware` in `config.json`.

## Time and cost

When an issue is resolved (Gate B is approved, or `finish` closes it), the script records how long it took and what it cost, and adds a line to `.issue-pipeline/ledger.jsonl`. `.claude/pipeline/run ledger` lists every resolved issue with the totals, and `.claude/pipeline/run cost <case>` shows a running case so far.

- **Time.** From the first event of the iteration to its close. "Working" leaves out the time spent waiting for you: before each approval you gave, and while the case was blocked.
- **Cost.** The model requests in the transcripts of the case's agents, and of your session between its first and last event of the case, at the prices under `prices` in `config.json` (cache writes and reads included, each request counted once). This is exact for what the transcripts record.
- **Estimate.** Claude Code's own side calls (permission checks in auto mode, compaction, titles) are not in the transcripts. Once a session has saved its total (on exit or resume), the estimate scales each session's share by that session's ratio of the total to the recorded requests. Run each issue in its own session for the cleanest numbers.

## Guided mode and auto mode

The pipeline runs in guided mode by default: Gates 0, A and B wait for you, and a stop asks you what to do. A stop comes only for a crucial question, after everything that does not depend on the answer is done: it names the options, what each costs and a recommendation, and the work continues with your answer.

Auto mode runs until the case is closed with the code on its branch, next to the approved `issue.md` and `design.md`. Nobody is asked and nothing waits:

- **The verdict is always `full`.** Auto mode builds every issue, also one that only hardware can verify. The report says what was not verified.
- **Gates.** The script takes a gate when its checks pass, and records the approval as made by `auto`.
- **Decisions instead of questions.** Every crucial question that guided mode would ask you is answered with the recommendation and recorded as a `**Decision:**` bullet. `report.md` lists them all under "Decisions", which the script checks, so you can review the decisions instead of the whole change.
- **No stops.** Every refusal of the script names what auto mode does instead. A role that cannot decide is told to decide and record its decision. Checks that still fail after three fixes (`caps.fixes`), a checkout that cannot be built, and an agent budget that is used up are listed in the report as accepted failures, and the run goes on. Once code is on the branch, `run finish <case>` closes the case with what exists.
- **Enforced by hooks.** While the case is open and no pipeline agent or command runs, a Stop hook in `/new-issue`, `/resolve-issue` and `/fix-ci` sends the session back to work with the next step, up to `auto_stop_limit` reminders without progress. Questions to you are refused.

Start it with `/new-issue --auto <issue link or description>`, which shapes the issue and goes straight on, or with `/resolve-issue <case> --auto`. For every new case, set `"mode": "auto"` in `config.json`. Gate C (changes to the agent files) always waits for you, and so does a gate you set to `"user"` under `gates`.

Three things auto mode cannot take over: Claude Code's permission prompts (run the session in a permission mode that does not prompt), an API error that ends the turn (`/resolve-issue --resume <case>` continues), and an issue link that cannot be fetched. It does not reserve machines either: a target without a reservation is listed in the report as not tested.

## Who is who

| Role | File you edit | Runs as | Model | Tools |
|---|---|---|---|---|
| Issue shaper | `.claude/skills/new-issue/SKILL.md` (also holds the issue format) | your session | your session's | all of your session's tools |
| Orchestrator | `.claude/skills/resolve-issue/SKILL.md` | your session | your session's | all of your session's tools |
| Triager | `.claude/agents/triager.md` | subagent | `sonnet` | read, write `triage.md` |
| Investigator | `.claude/agents/investigator.md` | subagent | `sonnet` | read, search, read-only git, Glean |
| Planner | `.claude/agents/planner.md` | subagent | `fable` | read, write `design.md` and `plan.md` |
| Reviewer | `.claude/agents/reviewer.md`, on top of `.github/skills/tt-exalens-review/SKILL.md` | subagent | `sonnet` | read, write its review |
| Test writer | `.claude/agents/test-writer.md` | subagent | `opus` | read, search, edit `test/`, run checks |
| Implementer | `.claude/agents/implementer.md`, on top of `AGENTS.md` | subagent | `opus` | read, search, edit outside `test/`, run checks |
| Papa | `.claude/agents/papa.md` | subagent | your session's | read, search, write proposals |

Rules shared by all roles are in `CONSTITUTION.md` in this directory. To change how a role behaves, edit its file rather than its output. `/papa` proposes such edits from what you corrected.

**Triage.** An existing issue, given by link, is triaged before it is shaped. The triager decides from the issue and the investigator's findings: `feature` (also tasks, docs and investigations) and `bug-confirmed` go on to the shaper. `bug-unconfirmed` and `bug-fixed` stop the case in state `rejected`, in auto mode too, and `triage.md` says how to confirm the bug. A bug counts as confirmed only when cited code at the base commit produces it: agents never run anything on hardware, so a bug only hardware can show stops as unconfirmed. Gate 0 refuses an existing issue without a triage. `advance <case> triage` triages again.

**Facts.** Only the investigator searches the code, its history and Glean. Only the triager, the shaper, the planner and the reviewer may ask it, and the orchestrator carries their questions. `run spawn` refuses any other requester. The planner and the reviewer have no search tools. The test writer and the implementer work in the code they change and report a missing fact as a gap in the plan.

**Glean.** The investigator uses the MCP server named `glean_default`, through `search`, `code_search` and `read_document` only. If your server has another name, change the `mcp__glean_default__*` entries in `investigator.md`. Without Glean the investigator still works and says so in its findings.

## Models

- **Subagents:** the `model:` line at the top of each file in `.claude/agents/`. Use an alias (`sonnet`, `opus`, `haiku`, `fable`), a full model id, or `inherit` for the model of your session. An `effort:` line works the same way.
- **Orchestrator and shaper:** they are your chat session, so they run on its model. Pick it with `/model` before you start.
- The file decides. The orchestrator cannot start a role on another model: a start that passes a model is refused. To try another model, change the file.

`run.jsonl` in each case records the model and the version of the role file for every agent start, and `status` shows the model each agent actually ran on.

## Context limit

No agent's context may exceed 500k tokens. The pipeline keeps it far below that by giving each agent a small task, and enforces the cap in three layers (`context` in `config.json`):

1. **Small tasks.** An investigator gets one narrow question. Findings are limited to 1200 words and the plan to 2500, and roles get an index of the findings instead of every file. Files over 24 kB are read in ranges of at most 400 lines.
2. **A budget per agent.** A hook measures an agent's context before each tool call. At 350k tokens, or at the role's tool-call limit, it may only write its output: it returns `RESULT: partial` and a fresh agent continues from the file. At 450k every tool call is refused. An agent is continued only while it holds less than 200k tokens. Otherwise a fresh one starts from the files.
3. **Compaction as the last line.** Each agent file sets `autoCompactWindow: 500000`, so Claude Code compacts an agent that would still reach the cap.

Your own session is the orchestrator, and the pipeline refuses to start a role from a session that holds more than 500k tokens. Run `/autocompact 500k` once, so that your sessions compact themselves at the cap: the case state is in files, and the orchestrator re-reads it afterwards. A lower effort level also keeps a session small, because the model's own reasoning stays in its context. Starting `/resolve-issue` in a new session after Gate 0 helps too.

`status` lists the largest agent contexts of a case and the size of the current session.

## Where things live

Runtime data is in `.issue-pipeline/` at the repository root. The directory ignores itself, so git never sees it. `git clean -x` would delete it. Set `home` in `config.json`, or `ISSUE_PIPELINE_HOME`, to move it.

    .issue-pipeline/
      cases/<case>/        status.json, issue.md, issue.notes.md, findings/, design.md, plan.md, feedback/, review/,
                           tests.md, impl-report.md, gates/, hardware/, report.md, pr-text.md, pr-description.md,
                           outcome.md, run.jsonl
      checkouts/<case>/    a clone of the base history only, without a remote, on the case branch
      hardware/            local/: the checkout this host builds for Quasar runs; machines.txt: machine names the
                           leak scan looks for
      ledger.jsonl         one line per resolved issue: time and cost
      budget/              one file per agent: tool calls, context size, model
      proposals/           papa's patches
      leak-patterns.txt    your own patterns for the leak scan, one regular expression per line

The clone starts from `base_ref` in `config.json`. Type checks and tests need the native module there: `run provision <case>` copies it from your working tree when the native sources match, and otherwise you run `make` in the checkout.

`config.json` also holds the loop caps, the tests that run without a device, the leak patterns that are safe to publish, and the optional path of a local tt-metal checkout for the investigator.

## Checks

`run` is the deterministic half: it keeps the case state, records approvals as hashes, and refuses steps whose preconditions do not hold. The agents cannot move a case past it.

| Check | When |
|---|---|
| `validate-issue`, `leak-scan` | before Gate 0: format, length limits, internal information |
| `validate-design` | before Gate A: `design.md` and `plan.md`, their limits, internal information in the design |
| `spawn` | before any role starts: right state, approved design, allowed requester, budget, session size |
| `commit` | the test writer commits only `test/`, the implementer never `test/` |
| `gates` | pre-commit, mypy, basedpyright, lib docs, device-free tests, on the committed state |
| `scope-check` | changed files against the plan's `## Files` list |
| `pr` | assembles the PR description, scans it, commits it with the issue and the design |
| `hw-list`, `hw-test` | your reservations; the case's tests and command examples on hardware. Only the orchestrator runs them |
| `cost`, `ledger` | time and dollars of a case so far; of every resolved issue |
| `guard` | a hook in each agent file and command file: writes, commands, reads and starts outside the limits are blocked, an agent sees only its own case, and a writing role runs only `test`, `commit`, `gates`, `env-check`, `scope-check` and `status` |
| `guard-stop` | a Stop hook in the command files: an auto-mode session keeps working until its case is closed |
| `build`, `finish` | copy or build the native module in the checkout; close an auto-mode case with the code that exists |

The hooks run only in a trusted workspace. To avoid a permission prompt per check, allow `Bash(.claude/pipeline/run *)` in `.claude/settings.local.json`.

## Changing the pipeline

- **A role's behaviour:** its file. Add a changelog line.
- **The issue format:** `.claude/skills/new-issue/SKILL.md`, and `ISSUE_SECTIONS` in `pipeline.py`, which the validator uses.
- **The design and plan formats:** `.claude/agents/planner.md`, and `DESIGN_SECTIONS` and `PLAN_SECTIONS` in `pipeline.py`.
- **Labels:** `labels.txt`. The pipeline never reads labels from GitHub.
- **Caps, limits, the context budget and the device-free test list:** `config.json`.
