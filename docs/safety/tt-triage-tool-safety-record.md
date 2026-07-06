# Tooling Safety Record — tt-triage

| Field | Value |
|---|---|
| Tool name | tt-triage |
| Tool owner | Aleksandar Dordevic, Ognjen Nenezic |
| Tool class | T4 (not used for safety verification) |
| In scope | No — diagnostic/convenience tool, not part of the safety argument or release-acceptance path |
| Intended use | Runs a series of checks/scripts to diagnose failures/hangs and provide insight into system state; consumes tt-exalens and Inspector data |
| Workflow stage | Post-failure diagnosis / debugging (incl. CI auto-triage of hangs) |
| Inputs | Inspector data, tt-exalens context, live device state |
| Outputs | Diagnostics report and device state dump |
| Safety impact if wrong | None on release acceptance — output is diagnostic only, never used as verification evidence or a release gate. A wrong diagnosis misleads debugging but does not change delivered behavior or safety evidence |
| Independent check | Diagnostics are not done with other tooling |
| Version | Part of tt-metal (`tools/triage/`); follows tt-metal, not separately versioned |
| Configuration lock | N/A - goes with tt-metal, figure out that |
| Evidence produced | TT-triage tests |
| Evidence location | tt-metal/tools/tests/triage/test_triage.py |
| Usage constraints | Must not be used as a source of safety/verification evidence |
| Qualification rationale | Out of scope — convenience/diagnostic tool that runs after a failure to aid debugging; not part of the safety argument or release-acceptance path |
| Status | Draft |
| Last review date | 2026-07-06 |
