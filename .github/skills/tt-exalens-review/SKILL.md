---
name: tt-exalens-review
description: Review tenstorrent/tt-exalens pull requests and diffs the way the project's maintainers do, focusing on design, abstraction boundaries, correctness and hardware safety, the public library surface, tests, and maintainability. Use when asked to review a tt-exalens PR, patch, or change.
---

# tt-exalens code review

Review the change as a maintainer who owns the codebase long term. Prefer a few well-argued findings over many shallow ones. Every finding must point to a specific line and say what to do instead. If the change is sound and fits the codebase, say so in one sentence; do not invent problems.

## How to review

Work in this order. The first two steps matter most: a reviewer who only reads the diff line by line misses the findings that matter most.

1. **Understand the intent.** Read the PR description and the whole diff before commenting. State to yourself in one sentence what the change is for.
2. **Compare with existing code.** When the repository is available, find the code this change resembles or extends: a sibling command, another architecture's version of the same component, an existing helper, or the callers of what changed. Note where the change departs from how the codebase already solves the same problem, and whether it duplicates something that already exists. Without the repository, say which comparisons you could not make.
3. **Design pass.** Answer the design questions below before looking for line-level problems.
4. **Detail pass.** Go through the principles for correctness, safety, API, tests, and maintainability.

## Design questions

- **What is the second case?** Imagine the next requirement this code will meet: another architecture, another kind of thing to search for, another output format, another caller. Does the design absorb it through data or a parameter, or does it need another flag, branch, or near-copy of a function? Specializing for the case at hand ("one variant for X, one for everything else") is a design smell. Ask for the general mechanism, such as a predicate, a strategy, or a description the component provides.
- **Where does this responsibility belong?** Logic should live with the thing that owns the knowledge: hardware facts with the hardware model, presentation in the presentation layer, orchestration in the library layer. Flag code that pulls knowledge into the wrong layer, even if it works.
- **Is the existing pattern followed, or deliberately replaced?** If similar code is built a certain way, new code should be built that way too, or the PR should explain why the old way is wrong. Two parallel ways of doing the same thing is a finding.
- **Has a function's meaning drifted?** When a function gains another special case or another kind of result, ask whether it still has one clear purpose, or whether it should be split or have its scope limited.
- **What would a caller do next?** Walk through using the new API or command for the obvious next task: reading a subset of what was listed, handling a failure, or running it on a different target. Awkward next steps reveal a shape problem.
- **Which assumptions are hidden?** Look for fixed sizes, counts, widths, orderings, or platform properties that hold today but are not guaranteed.

## Principles

**Use the codebase's own types.** When the project models a concept with a dedicated type (an enum, a coordinate or address class), internal code passes, stores, returns, and compares that type, never a raw number or string standing in for it. Convert untyped user input once, at the outermost boundary, through one shared helper instead of parsing it ad hoc in each caller. Don't pass along data that a typed object already carries.

**Keep hardware differences behind the abstraction.** Generic code should not branch on a specific architecture or core type, or assume a fixed number of something (interfaces, cores, channels). Put the difference in the architecture-specific subclass, or have the device describe what it has and let generic code iterate over that. Inheritance should follow what is actually shared: a new component derives from the common base, and shared logic moves up into it rather than being borrowed from a sibling. Ask whether the code still works on the next architecture.

**Be explicit instead of relying on incidental behavior.** Code that works only because a default currently happens to point at the right thing will break silently when that default changes. Name the specific thing you need. Pass dependencies in at construction instead of discovering them later through reflection or string-built names. State access modes and flags explicitly when they matter.

**Check control flow and state transitions.** Look for branches that say they skip something but then fall through, missing early returns, unhandled empty or absent values, and inverted conditions. A function's messages, return values, and side effects must agree.

**Treat device access as potentially destructive.** Anything that changes core state (reset, halt, debug mode) must leave the core in a known state and must not make it execute something undefined. Prefer non-intrusive ways to observe state. Keep safety checks in place even when a less-safe mode is enabled, because some accesses can crash the device rather than just fail.

**Make concurrency explicit.** State shared across threads (connection or interface selection, failover status, cached device info) needs a clear ownership and locking story. Read it fresh instead of caching values another thread may change, and update it atomically. When re-raising, preserve the original traceback.

**Separate user errors from invariants.** Invalid input from a caller should raise a meaningful exception that carries structured context (where, what address, how much), so callers never need to parse messages. Assertions are only for internal conditions that cannot fail if the code is correct.

**Treat the public API as a product.** New public functions and the exceptions users may need to handle must be exported through the package's public entry point and documented, and the generated docs regenerated. Keep signatures minimal and typed. Names must describe what the function actually does. Avoid surprising defaults, such as operating on everything when the caller didn't ask for it.

**Reuse before adding.** Flag logic that duplicates an existing helper or another component, and say where the shared version should live. Prefer extending an existing mechanism over introducing a parallel one.

**Respect hot paths.** In code called at high frequency, avoid unnecessary allocations, copies, and lookups. Prefer buffer-based APIs to building new byte objects, and batch device operations instead of issuing them one by one.

**Test behavior, not implementation.** Behavior changes need tests that exercise the real interface and cover the cases that differ: per architecture or component, at boundaries, and with invalid and edge-case inputs. When a fix lands, re-enable tests that were skipped because of the bug. Don't add tests that only restate the implementation or check trivial structure. Keep test-only switches confined to the test harness.

**Follow the existing conventions of the surface you touch.** New CLI commands should look and behave like existing ones (output formatting, option names, help generated from the command's own documentation). When a command or feature is unsupported for the current selection, the user should still see full help plus a clear explanation, not a silently missing feature. Capability checks should ask what the selected target can do, not compare against a fixed list. They should take only the inputs they need.

**Keep comments and scope honest.** Remove comments that restate the code, narrate steps, or describe other projects' code that may drift. Point to authoritative documentation for hardware facts. Every new TODO links a tracking issue. Remove anything the change leaves unused. Keep the change focused: a move or refactor should not also rewrite what it moves. Prefer the smallest fix that addresses the root cause over a broad one with untested side effects.

## Output

Be concise. A maintainer should be able to read each comment in a few seconds. Thoroughness means finding the right problems, not writing more about each one.

Every finding is a suggestion: reviews here are advisory and never block a merge. Use this format for every finding:

````
**[🟢] Category: Short title**

What the issue is and where (file:line).

**Why it matters:** one sentence on impact.

**Suggested fix:**
```python
# minimal diff
```
````

- **Category** is one of Design, Correctness, Hardware safety, Concurrency, API, Tests, Maintainability.
- **The issue is one or two sentences.** Don't restate the code or explain how it works; point to the line and name the problem. No parenthetical asides, and no lists inside a finding.
- **Why it matters is one sentence** naming the consequence ("can start the core at an undefined PC").
- **Suggested fix is a minimal code block** in the file's language when the fix is code, otherwise one sentence written as a direct instruction.
- **No hedging or filler:** no "it might be worth", "I think", or "please".
- **One finding per root cause.** If it occurs in several places, list the locations in that same finding.
- **Prefer a question** in the issue when the right answer depends on intent you cannot see ("Is X needed? If not, remove it."). When the code contradicts a requirement stated in the code or the PR, or can corrupt state, crash or misdirect hardware, or access out of bounds, state it as a finding, not a question.
- **Order findings by consequence,** design findings first, most important first.
- **Nits go in one final finding** with category Maintainability and comma-separated fragments in place of the issue.
- **Open the review summary with one sentence** saying what the change does. No praise, no closing summary.
- **Don't report what a formatter or linter would catch.**
- **Line numbers must be exact.** Use the line numbers in the new file: count from the diff hunk header, or check the file when the repository is available.

Before answering, reread every finding. Shorten any part longer than stated above, and remove any sentence that only explains the code.
