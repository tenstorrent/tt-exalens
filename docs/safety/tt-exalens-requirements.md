# Preliminary High-Level Requirements — tt-exalens

## Preliminary requirement set

#### EXALENS-HLR-001
tt-exalens shall provide supported low-level device-access, debug, and ELF-loading behavior within the defined AI-IP software scope.

#### EXALENS-HLR-002
tt-exalens shall accept device-access, debug, and ELF-load requests only through its defined supported library and CLI interfaces.

#### EXALENS-HLR-003
tt-exalens shall validate the required preconditions for a safety-relevant ELF load — including the target RISC core being in reset, the presence of the required loadable sections, and correct address alignment — before performing the load.

#### EXALENS-HLR-004
When loading an ELF onto a RISC-V core, tt-exalens shall write the defined loadable sections to the addresses specified by the ELF, including correct handling of memory regions that are not directly accessible over NOC.

#### EXALENS-HLR-005
tt-exalens shall provide an independent read-back verification of safety-relevant ELF-load writes and shall compare the written data against the intended ELF section data.

#### EXALENS-HLR-006
tt-exalens shall return or expose status, data, and error information for supported operations through defined reporting paths.

#### EXALENS-HLR-007
tt-exalens shall not silently continue, nor report success for, a safety-relevant ELF load when a section fails to write or fails read-back verification, or when a required precondition is invalid, unavailable, or inconsistent for the intended mode.

#### EXALENS-HLR-008
tt-exalens shall operate against a frozen, identifiable version and configuration whenever it is used to produce or support safety-relevant evidence.

#### EXALENS-HLR-009
tt-exalens shall preserve the separation between its safety-relevant surface (the ELF-load path consumed by LLK) and its convenience-only debug and introspection features.

#### EXALENS-HLR-010
tt-exalens shall preserve and document its assumptions of use, boundary dependencies, and supported operating constraints so that later safety analysis, verification planning, and variant-specific tailoring can be performed in a controlled manner.
