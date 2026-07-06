# Preliminary High-Level Requirements — DPRINT / DEVICE_PRINT

## Preliminary requirement set

#### DPRINT-HLR-001
DPRINT / DEVICE_PRINT shall provide supported device-side debug-print behavior within the defined AI-IP software scope.

#### DPRINT-HLR-002
DPRINT / DEVICE_PRINT shall be invoked only through its defined device-side API from kernel/firmware code and configured only through its defined host-side controls.

#### DPRINT-HLR-003
When device printing is not enabled, DPRINT / DEVICE_PRINT shall compile to no operation and shall have no runtime effect on the program under test.

#### DPRINT-HLR-004
When enabled, DPRINT / DEVICE_PRINT shall transfer the requested values from the device to the host and present them through the defined print output.

#### DPRINT-HLR-005
DPRINT / DEVICE_PRINT shall not alter the functional results of the kernel or firmware under test beyond its documented device resource usage (print buffer and memory footprint).

#### DPRINT-HLR-006
DPRINT / DEVICE_PRINT shall behave in a defined, documented manner when the print buffer is full or the host print server is unavailable, rather than corrupting or misrepresenting delivered output.

#### DPRINT-HLR-007
DPRINT / DEVICE_PRINT output shall not be used as a safety-verification pass/fail criterion or as release-acceptance evidence; where a test's verdict depends on printed values, that usage shall be reclassified and controlled as an in-scope (T2) verification tool.

#### DPRINT-HLR-008
DPRINT / DEVICE_PRINT shall preserve and document its assumptions of use, resource constraints, and supported operating constraints so that later safety analysis, verification planning, and variant-specific tailoring can be performed in a controlled manner.
