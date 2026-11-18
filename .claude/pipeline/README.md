# Issue pipeline

A set of Claude Code agents that take a tt-exalens change from a rough description to a reviewed local branch with a pull request description. Everything stays on your machine: the agents never push, never write to GitHub, and never touch a device or simulator. You approve the issue, the design and the result, and you publish. If you switch a case to auto mode, the script takes those approvals for you.

## Using it

Start a new Claude Code session in the repository, so that the agent files are loaded. Then:

| Command | What it does |
|---|---|
| `/new-issue <description, issue link or file>` | Shapes a short issue with you and stops at Gate 0 |
| `/resolve-issue <case>` | Investigates, designs (Gate A), writes tests, implements, reviews once, reports (Gate B) |
| `/fix-ci <case> <log file>` | Another round after you pushed and CI failed |
| `/papa [case ...]` | Proposes changes to the agent files from closed cases (Gate C) |

At a gate the session shows a document and its hash and waits. You edit the file or give feedback, and you approve with `approve <hash>`. If you edit the file, the hash changes, so an approval always names the version you read.

`.claude/pipeline/run status` lists the cases. `.claude/pipeline/run status <case>` shows where one stands and what comes next. `/resolve-issue --resume <case>` continues after an interruption.

## What you read

The documents written for you are short, and the script refuses them over their limits (`limits` in `config.json`).

| Document | Gate | What it says | Limit |
|---|---|---|---|
| `issue.md` | 0 | The problem and what done looks like, with at most five acceptance criteria | 250 words |
| `design.md` | A | What the change achieves, the API it changes, the modules and classes it adds | 300 words |
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

## Guided mode and auto mode

The pipeline runs in guided mode by default: Gates 0, A and B wait for you, and a stop asks you what to do.

In auto mode nobody is asked. The shaper asks no questions and records its assumptions in `issue.notes.md`. The script takes a gate when its checks pass, and records the approval as made by `auto`. A stop ends the run with a message instead of a question. Nothing is pushed in either mode.

- **One run:** `/new-issue --auto <description>` or `/resolve-issue <case> --auto`, or tell the session "auto mode". It runs `.claude/pipeline/run mode <case> auto`.
- **Every new case:** `"mode": "auto"` in `config.json`.
- **Keeping a gate for yourself in auto mode:** set it to `"user"` under `gates` in `config.json`. Gate C (changes to the agent files) always waits for you.

Auto mode covers the pipeline's own questions. Claude Code's permission prompts are separate: an unattended run also needs a permission mode that does not prompt for the commands the agents run.

## Who is who

| Role | File you edit | Runs as | Model | Tools |
|---|---|---|---|---|
| Issue shaper | `.claude/skills/new-issue/SKILL.md` (also holds the issue format) | your session | your session's | all of your session's tools |
| Orchestrator | `.claude/skills/resolve-issue/SKILL.md` | your session | your session's | all of your session's tools |
| Investigator | `.claude/agents/investigator.md` | subagent | `sonnet` | read, search, read-only git, Glean |
| Planner | `.claude/agents/planner.md` | subagent | `fable` | read, write `design.md` and `plan.md` |
| Reviewer | `.claude/agents/reviewer.md`, on top of `.github/skills/tt-exalens-review/SKILL.md` | subagent | `fable` | read, write its review |
| Test writer | `.claude/agents/test-writer.md` | subagent | `opus` | read, search, edit `test/`, run checks |
| Implementer | `.claude/agents/implementer.md`, on top of `AGENTS.md` | subagent | `opus` | read, search, edit outside `test/`, run checks |
| Papa | `.claude/agents/papa.md` | subagent | your session's | read, search, write proposals |

Rules shared by all roles are in `CONSTITUTION.md` in this directory. To change how a role behaves, edit its file rather than its output. `/papa` proposes such edits from what you corrected.

**Facts.** Only the investigator searches the code, its history and Glean. Only the shaper, the planner and the reviewer may ask it, and the orchestrator carries their questions. `run spawn` refuses any other requester. The planner and the reviewer have no search tools. The test writer and the implementer work in the code they change and report a missing fact as a gap in the plan.

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
                           tests.md, impl-report.md, gates/, report.md, pr-text.md, pr-description.md, outcome.md, run.jsonl
      checkouts/<case>/    a clone without a remote, on the case branch
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
| `guard` | a hook in each agent file and command file: writes, commands, reads and starts outside the limits are blocked |

The hooks run only in a trusted workspace. To avoid a permission prompt per check, allow `Bash(.claude/pipeline/run *)` in `.claude/settings.local.json`.

## Changing the pipeline

- **A role's behaviour:** its file. Add a changelog line.
- **The issue format:** `.claude/skills/new-issue/SKILL.md`, and `ISSUE_SECTIONS` in `pipeline.py`, which the validator uses.
- **The design and plan formats:** `.claude/agents/planner.md`, and `DESIGN_SECTIONS` and `PLAN_SECTIONS` in `pipeline.py`.
- **Labels:** `labels.txt`. The pipeline never reads labels from GitHub.
- **Caps, limits, the context budget and the device-free test list:** `config.json`.
