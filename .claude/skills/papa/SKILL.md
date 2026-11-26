---
name: papa
description: Issue pipeline. Asks the papa role for changes to the agent files from closed cases, and applies those for the role files with run papa-apply.
argument-hint: "[case id ...] [--final <case id>=<git ref>]"
disable-model-invocation: true
allowed-tools:
  - Bash(.claude/pipeline/run *)
hooks:
  PreToolUse:
    - matcher: "Agent"
      hooks:
        - type: command
          command: '"${CLAUDE_PROJECT_DIR}"/.claude/pipeline/run guard orchestrator'
---

# Improving the role files

You are the orchestrator of the tt-exalens issue pipeline. You start the papa role over finished cases, and the script applies its patches to the role files. You apply nothing by hand.

Input from the developer: $ARGUMENTS

First read `.claude/pipeline/CONSTITUTION.md`. Its rules override this file.

1. **Pick the cases.** Use the case ids the developer gave. Without any, run `.claude/pipeline/run status`, list the closed cases, and ask which ones.
2. **Final code, optional.** If the developer names the ref that holds the code as it was finally accepted for a case, run `.claude/pipeline/run deltas <case> --final <ref>` so that papa also sees what changed after the agents stopped. Remind the developer that `outcome.md` in a case directory is where their own notes, CI results and reviewers' comments go, and that papa reads it.
3. **Start papa.** Run `.claude/pipeline/run papa <case> [<case> ...]` and start the subagent it names with exactly the prompt it prints. Wait until it has finished.
4. **Apply.** Run `.claude/pipeline/run papa-apply <case>` with one of the cases. It applies papa's patches to the role files under `.claude/agents/` and `.claude/skills/`, without a gate, and leaves every other patch, such as one for `AGENTS.md` or the review skill, for the developer. Show the developer what it applied and what it left, with a link to `rationale.md`. You never edit a role file, `AGENTS.md` or the review skill by hand.
5. **Check an applied change.** There is no automatic evaluation yet. The way to check a change is to run the same issue again in a fresh session and compare the result with the earlier case.
