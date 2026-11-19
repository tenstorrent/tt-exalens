# [cli] Make debug-bus read past combined signals and reject an explicit 0 for group sampling

## Summary
In `debug-bus`, a combined signal ends the rest of a signal list, and an explicit `0` for group sampling options silently becomes a default, so users get data they did not ask for.

## Current behavior
Combined signals have parts, e.g. `brisc_if_ex_deco` (Wormhole).
```
debug-bus brisc_if_ex_deco,trisc0_pc
debug-bus group <group> 0x1000 --samples 0
debug-bus group <group> 0x1000 --samples 4 --sampling-interval 0
```
1. Prints the warning and part names, then stops: no `trisc0_pc`, at any `-l` location.
2. Captures 1 sample.
3. Samples every 2 cycles.

## Desired behavior
The rest of the list is read after a combined signal's warning. An explicit `0` is validated and rejected like any out-of-range value; omitted options keep their defaults.

## Acceptance criteria
- When `debug-bus trisc0_pc,<combined>,trisc1_pc` runs, then the combined signal's warning and part names appear, and `trisc0_pc` and `trisc1_pc` are printed.
- When that list runs with two `-l` locations, then `trisc0_pc` and `trisc1_pc` are printed at each location.
- When `group` runs with `--samples 0`, then the command reports an error containing "samples count must be at least 1", without device access.
- When `group` runs with `--samples 4 --sampling-interval 0`, then it reports an error containing "sampling_interval must be between 2 and 256", without device access.
- When both options are omitted, then the group read is requested with 1 sample and interval 2, as before.

## Scope
The `debug-bus` CLI command: signal-list reading and the `group` subcommand, on Wormhole and Blackhole.

## Out of scope
Reading combined signals, the validation ranges, the interval when one sample is taken.

## Verification
Device-free tests with a stand-in device; optionally the commands above on a board.

## Environment
Not stated. The code is architecture-independent; present on main at ab935eeaa.
