# Issue pipeline

A set of Claude Code agents that take a tt-exalens change from a rough description to a reviewed local branch. Everything stays on your machine: the agents never push, never write to GitHub, and never touch a device or simulator. You approve the issue, the plan and the result, and you publish.

## Using it

Start a new Claude Code session in the repository, so that the agent files are loaded. Then:

| Command | What it does |
|---|---|
| `/new-issue <description, issue link or file>` | Shapes an issue with you and stops at Gate 0 |
| `/resolve-issue <case>` | Investigates, plans (Gate A), writes tests, implements, reviews, reports (Gate B) |
| `/fix-ci <case> <log file>` | Another round after you pushed and CI failed |
| `/papa [case ...]` | Proposes changes to the agent files from closed cases (Gate C) |

At a gate the session shows an artifact and its hash and waits. You edit the file or give feedback, and you approve with `approve <hash>`. If you edit the file, the hash changes, so an approval always names the version you read.

`.claude/pipeline/run status` lists the cases. `.claude/pipeline/run status <case>` shows where one stands and what comes next. `/resolve-issue --resume <case>` continues after an interruption.

## Who is who

| Role | File you edit | Runs as | Tools |
|---|---|---|---|
| Issue shaper | `.claude/skills/new-issue/SKILL.md` (also holds the issue format) | your session | all of your session's tools |
| Orchestrator | `.claude/skills/resolve-issue/SKILL.md` | your session | all of your session's tools |
| Investigator | `.claude/agents/investigator.md` | subagent | read, search, read-only git, Glean |
| Planner | `.claude/agents/planner.md` | subagent | read, write `plan.md` |
| Reviewer | `.claude/agents/reviewer.md`, on top of `.github/skills/tt-exalens-review/SKILL.md` | subagent | read, write its review |
| Test writer | `.claude/agents/test-writer.md` | subagent | read, search, edit `test/`, run checks |
| Implementer | `.claude/agents/implementer.md`, on top of `AGENTS.md` | subagent | read, search, edit outside `test/`, run checks |
| Papa | `.claude/agents/papa.md` | subagent | read, search, write proposals |

Rules shared by all roles are in `CONSTITUTION.md` in this directory. To change how a role behaves, edit its file rather than its output. `/papa` proposes such edits from what you corrected.

**Facts.** Only the investigator searches the code, its history and Glean. Only the shaper, the planner and the reviewer may ask it, and the orchestrator carries their questions. `run spawn` refuses any other requester. The planner and the reviewer have no search tools. The test writer and the implementer work in the code they change and report a missing fact as a gap in the plan.

**Glean.** The investigator uses the MCP server named `glean_default`, through `search`, `code_search` and `read_document` only. If your server has another name, change the three `mcp__glean_default__*` entries in `investigator.md`. Without Glean the investigator still works and says so in its findings.

## Choosing models

- **Subagents:** the `model:` line at the top of each file in `.claude/agents/`. Use `inherit` (the model of your session, the default here), an alias such as `opus`, `sonnet`, `haiku` or `fable`, or a full model id. An `effort:` line works the same way.
- **Orchestrator and shaper:** they are your chat session, so they run on its model. Pick it with `/model` before you start. A `model:` line in a `SKILL.md` would only last for the turn in which you type the command.
- **One run:** tell the orchestrator, for example "use opus for the planner this time".
- `CLAUDE_CODE_SUBAGENT_MODEL` does not override a `model:` line, not even `inherit`. It applies only to a role whose `model:` line is removed.

`run.jsonl` in each case records the model and the version of the role file for every agent start.

## Guided mode and auto mode

The pipeline runs in guided mode: Gates 0, A, B and C wait for you, and loops stop at their caps and ask. Auto mode is not built. The places reserved for it:

- `mode` and `gates` in `config.json`. `run approve` refuses anything but `guided` and `user`.
- `--by` on `run approve`, which records who approved.
- The "Gate" sections of the four command files, which are the only places that describe how a gate is taken.

A replay evaluation of the role files (`/eval` in the design) needs gates that answer themselves, so it waits for auto mode too.

## Where things live

Runtime data is in `.issue-pipeline/` at the repository root. The directory ignores itself, so git never sees it. `git clean -x` would delete it. Set `home` in `config.json`, or `ISSUE_PIPELINE_HOME`, to move it.

    .issue-pipeline/
      cases/<case>/        status.json, issue.md, issue.notes.md, findings/, plan.md, feedback/, review/,
                           tests.md, impl-report.md, gates/, report.md, pr-text.md, outcome.md, run.jsonl
      checkouts/<case>/    a clone without a remote, on the branch agent/<case>
      proposals/           papa's patches
      leak-patterns.txt    your own patterns for the leak scan, one regular expression per line

Agents work in the case checkout, never in your working tree. It starts from `base_ref` in `config.json`. Type checks and tests need the native module there: `run provision <case>` copies it from your working tree when the native sources match, and otherwise you run `make` in the checkout. To take a finished branch: `git fetch .issue-pipeline/checkouts/<case> agent/<case>:<branch name>`.

`config.json` also holds the loop caps, the tests that run without a device, the leak patterns that are safe to publish, and the optional path of a local tt-metal checkout for the investigator.

## Checks

`run` is the deterministic half: it keeps the case state, records approvals as hashes, and refuses steps whose preconditions do not hold. The agents cannot move a case past it.

| Check | When |
|---|---|
| `validate-issue`, `leak-scan` | before Gate 0. The leak scan runs again before Gate B, over the PR text, the branch diff and the commit messages |
| `spawn` | before any role starts: right state, approved plan, allowed requester, budget |
| `commit` | the test writer commits only `test/`, the implementer never `test/` |
| `gates` | pre-commit, mypy, basedpyright, lib docs, device-free tests, on the committed state |
| `scope-check` | changed files against the plan's `## Files` list |
| `guard` | a hook in each agent file: writes and commands outside a role's limits are blocked |

The hooks run only in a trusted workspace. To avoid a permission prompt per check, allow `Bash(.claude/pipeline/run *)` in `.claude/settings.local.json`.

## Changing the pipeline

- **A role's behaviour:** its file. Add a changelog line.
- **The issue format:** `.claude/skills/new-issue/SKILL.md`, and `ISSUE_SECTIONS` in `pipeline.py`, which the validator uses.
- **The plan format:** `.claude/agents/planner.md`, and `PLAN_SECTIONS` in `pipeline.py`.
- **Labels:** `labels.txt`. The pipeline never reads labels from GitHub.
- **Caps and the device-free test list:** `config.json`.
