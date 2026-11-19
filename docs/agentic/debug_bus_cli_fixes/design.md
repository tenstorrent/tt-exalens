# Design: [cli] Make debug-bus read past combined signals and reject an explicit 0 for group sampling

## Scope
- `debug-bus <signals>`: a combined signal in the list still prints its warning and part names, and the signals after it are now read and printed, at every `-l` location.
- `debug-bus group ... --samples 0` is no longer turned into 1 sample. The value reaches the existing validation, which fails with "samples count must be at least 1" before any device access.
- `debug-bus group ... --samples 4 --sampling-interval 0` is no longer turned into interval 2. It fails with "sampling_interval must be between 2 and 256" before any device access.
- Omitted options keep their defaults: 1 sample, interval 2.

Left alone: how combined signals are read, the validation ranges and messages, how the error is displayed (the CLI's normal exception output, as for any other out-of-range value), the handling of `--sampling-interval` when one sample is taken, and the command's help text.

## API changes
None. The command syntax, options and help text of `debug-bus` are unchanged. Only two behaviours change:

- signal list: a combined signal is skipped after its warning instead of ending the list,
- `group`: an explicit `0` for `--samples` or `--sampling-interval` is passed on and rejected instead of being replaced by the default.

## New modules and classes
None. The change is confined to `ttexalens/cli_commands/debug_bus.py`. A device-free test class is added to the existing `test/ttexalens/unit_tests/test_debug_bus.py`.
