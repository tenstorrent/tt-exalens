# Tooling Safety Record — DPRINT / DEVICE_PRINT

| Field | Value |
|---|---|
| Tool name | DPRINT / DEVICE_PRINT (device-side debug print) |
| Tool owner | Aleksandar Dordevic, Vuk Jovanovic |
| Tool class | T4 (out of scope) |
| In scope | No — optional debug instrumentation, not a safety-claimed mechanism or release gate |
| Intended use | Device-side debug print API for kernels/firmware — prints values (scalars, addresses, buffer contents) from RISC cores back to host for debugging |
| Workflow stage | Kernel/firmware debugging; optional instrumentation in LLK tests (compiles to no-op when disabled) |
| Inputs | Variable names and string text |
| Outputs | Printed debug text to host (dprint log) |
| Safety impact if wrong | Diagnostic output only; not a pass/fail criterion. Wrong output misleads debugging |
| Independent check | N/A (out of scope) |
| Version | Part of tt-metal |
| Configuration lock | N/A |
| Evidence produced | DPRINT tests in tt-metal repo |
| Evidence location | https://github.com/tenstorrent/tt-metal/tree/main/tests/tt_metal/tt_metal/debug_tools/device_print |
| Usage constraints | Optional instrumentation; must not be relied upon as the correctness / pass-fail criterion |
| Qualification rationale | Out of scope — used in LLK test infra only as optional debug instrumentation around asserts; compiles to no-op when disabled; not a safety-claimed mechanism or release-acceptance gate |
| Status | Draft |
| Last review date | 2026-07-06 |
