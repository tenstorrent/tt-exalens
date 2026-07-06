# Preliminary High-Level Requirements — tt-triage

## Preliminary requirement set

#### TRIAGE-HLR-001
tt-triage shall provide supported post-failure diagnostic and system-state inspection behavior within the defined AI-IP software scope.

#### TRIAGE-HLR-002
tt-triage shall obtain device and system state only through its defined supported data providers (e.g. tt-exalens and Inspector).

#### TRIAGE-HLR-003
tt-triage shall validate required preconditions — including debugger-context initialization and availability of its data providers — before running a diagnostic or analysis script.

#### TRIAGE-HLR-004
tt-triage shall execute its diagnostic and analysis scripts and present the resulting diagnostics and device-state information to the user.

#### TRIAGE-HLR-005
tt-triage shall use read/observation-oriented access and shall not modify device or host state beyond documented, explicitly requested actions (e.g. an opt-in post-run device reset).

#### TRIAGE-HLR-006
tt-triage shall report diagnostic results, and any inability to collect required data, through its defined output paths.

#### TRIAGE-HLR-007
tt-triage shall not present a diagnosis as authoritative when required data could not be reliably collected or when the inspected state is inconsistent; such conditions shall be surfaced to the user.

#### TRIAGE-HLR-008
tt-triage output shall not be used as safety-verification evidence or as a release-acceptance criterion.

#### TRIAGE-HLR-009
tt-triage shall preserve and document its assumptions of use, boundary dependencies, and supported operating constraints so that later safety analysis, verification planning, and variant-specific tailoring can be performed in a controlled manner.
