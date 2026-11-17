---
name: papa
description: Issue pipeline. Asks the papa role to propose changes to the agent files from closed cases, and walks the developer through accepting or rejecting each proposal.
argument-hint: "[case id ...] [--final <case id>=<git ref>]"
disable-model-invocation: true
allowed-tools:
  - Bash(.claude/pipeline/run *)
---

# Improving the role files

You are the orchestrator of the tt-exalens issue pipeline. You start the papa role over finished cases and take its proposals to the developer. You apply nothing yourself.

Input from the developer: $ARGUMENTS

First read `.claude/pipeline/CONSTITUTION.md`. Its rules override this file.

1. **Pick the cases.** Use the case ids the developer gave. Without any, run `.claude/pipeline/run status`, list the closed cases, and ask which ones.
2. **Final code, optional.** If the developer names the ref that holds the code as it was finally accepted for a case, run `.claude/pipeline/run deltas <case> --final <ref>` so that papa also sees what changed after the agents stopped. Remind the developer that `outcome.md` in a case directory is where their own notes, CI results and reviewers' comments go, and that papa reads it.
3. **Start papa.** Run `.claude/pipeline/run papa <case> [<case> ...]` and start the subagent it names with exactly the prompt it prints. Wait until it has finished.
4. **Gate C.** Show a link to `rationale.md` and, for each proposal, one line: the target file, the change, the evidence and the size. The developer decides on each one, and applies the ones they accept themselves:

       git apply <proposals directory>/NN-<target>.patch

   You never apply a patch and never edit a role file, `AGENTS.md` or the review skill on papa's behalf. `gates.prompts` in `.claude/pipeline/config.json` is reserved for an auto mode that does not exist yet.
5. **Check an accepted change.** There is no automatic evaluation yet. The way to check a change is to run the same issue again in a fresh session and compare the result with the earlier case.
