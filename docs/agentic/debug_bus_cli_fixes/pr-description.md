# debug-bus: read past combined signals and reject an explicit 0 for group sampling

Two fixes in the `debug-bus` CLI command:

- A combined signal in a signal list still prints its warning and part names, and the rest of the list is now read at every location. Before, the handler returned and dropped every later signal.
- `debug-bus group` now applies the defaults of 1 sample and interval 2 only when `--samples` or `--sampling-interval` is omitted. An explicit `0` now reaches the existing validation and is rejected. Before, `or` turned it into the default.

New device-free tests in `TestDebugBusCommand` cover both fixes, using a real `DebugBusSignalStore` over a mocked NOC block.

## Verification
pre-commit, mypy, basedpyright, the lib docs check and the existing device-free tests pass.

**Not verified:** the new `TestDebugBusCommand` tests were loaded but not run. Run them with `python3 -m unittest test.ttexalens.unit_tests.test_debug_bus.TestDebugBusCommand`. Also not verified: the path through docopt, the device tests, and the commands on a Wormhole or Blackhole board.

Closes #1280

<details>
<summary>Issue: [cli] Make debug-bus read past combined signals and reject an explicit 0 for group sampling</summary>

#### Summary
In `debug-bus`, a combined signal ends the rest of a signal list, and an explicit `0` for group sampling options silently becomes a default, so users get data they did not ask for.

#### Current behavior
Combined signals have parts, e.g. `brisc_if_ex_deco` (Wormhole).
```
debug-bus brisc_if_ex_deco,trisc0_pc
debug-bus group <group> 0x1000 --samples 0
debug-bus group <group> 0x1000 --samples 4 --sampling-interval 0
```
1. Prints the warning and part names, then stops: no `trisc0_pc`, at any `-l` location.
2. Captures 1 sample.
3. Samples every 2 cycles.

#### Desired behavior
The rest of the list is read after a combined signal's warning. An explicit `0` is validated and rejected like any out-of-range value; omitted options keep their defaults.

#### Acceptance criteria
- When `debug-bus trisc0_pc,<combined>,trisc1_pc` runs, then the combined signal's warning and part names appear, and `trisc0_pc` and `trisc1_pc` are printed.
- When that list runs with two `-l` locations, then `trisc0_pc` and `trisc1_pc` are printed at each location.
- When `group` runs with `--samples 0`, then the command reports an error containing "samples count must be at least 1", without device access.
- When `group` runs with `--samples 4 --sampling-interval 0`, then it reports an error containing "sampling_interval must be between 2 and 256", without device access.
- When both options are omitted, then the group read is requested with 1 sample and interval 2, as before.

#### Scope
The `debug-bus` CLI command: signal-list reading and the `group` subcommand, on Wormhole and Blackhole.

#### Out of scope
Reading combined signals, the validation ranges, the interval when one sample is taken.

#### Verification
Device-free tests with a stand-in device; optionally the commands above on a board.

#### Environment
Not stated. The code is architecture-independent; present on main at ab935eeaa.

</details>

<details>
<summary>Design: [cli] Make debug-bus read past combined signals and reject an explicit 0 for group sampling</summary>

#### Scope
- `debug-bus <signals>`: a combined signal in the list still prints its warning and part names, and the signals after it are now read and printed, at every `-l` location.
- `debug-bus group ... --samples 0` is no longer turned into 1 sample. The value reaches the existing validation, which fails with "samples count must be at least 1" before any device access.
- `debug-bus group ... --samples 4 --sampling-interval 0` is no longer turned into interval 2. It fails with "sampling_interval must be between 2 and 256" before any device access.
- Omitted options keep their defaults: 1 sample, interval 2.

Left alone: how combined signals are read, the validation ranges and messages, how the error is displayed (the CLI's normal exception output, as for any other out-of-range value), the handling of `--sampling-interval` when one sample is taken, and the command's help text.

#### API changes
None. The command syntax, options and help text of `debug-bus` are unchanged. Only two behaviours change:

- signal list: a combined signal is skipped after its warning instead of ending the list,
- `group`: an explicit `0` for `--samples` or `--sampling-interval` is passed on and rejected instead of being replaced by the default.

#### New modules and classes
None. The change is confined to `ttexalens/cli_commands/debug_bus.py`. A device-free test class is added to the existing `test/ttexalens/unit_tests/test_debug_bus.py`.

</details>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
