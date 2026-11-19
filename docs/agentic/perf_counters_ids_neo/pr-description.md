# Read unnamed perf counter ids with --counter and reject NEO ids on Wormhole/Blackhole

`perf-counters read --block=<block> --counter=<id>` only matched ids that have a name in the block's map, so an id like FPU 2 printed "not found" although the usage text allows 0 to 511. The command now reads any id in that range through a new library function, `read_perf_counter`. It warns before any device access when the id is out of range.

On Wormhole and Blackhole, `read_perf_counters`, `reset_perf_counters`, `start_perf_counters` and `stop_perf_counters` used to accept a NEO id and silently act on the core's own counters. These cores have no NEOs, so `NocBlock.get_perf_counters` now returns None for a NEO id, as `get_debug_bus` already does, and the functions raise `TTException`. Quasar is unchanged.

## Verification
pre-commit, mypy and basedpyright pass. The lib docs are regenerated. The new tests in `test/ttexalens/unit_tests/test_perf_counters.py` load, but none has run yet.
**Hardware:** Wormhole: not tested, the machine did not answer. Blackhole: not tested, no reservation. Quasar: not tested, the board or the emulator was busy.
**Not verified:** the new tests, the `perf-counters` examples, and regenerating `docs/ttexalens-app-docs.md`.

Closes #1278

<details>
<summary>Issue: [lib] Read unnamed perf counter ids with --counter and reject NEO ids on Wormhole/Blackhole</summary>

#### Summary
`perf-counters read --counter` cannot read counter ids missing from the block's name map, although usage allows 0 to 511. On Wormhole and Blackhole, the perf-counter library functions silently accept a NEO id.

#### Current behavior
FPU names only ids 0, 1 and 257, so counter 2 is never read:

```
perf-counters read --block=FPU --counter=2
counter 2 not found in block FPU
```

On Wormhole and Blackhole, which have no NEOs, `read_perf_counters(loc, neo_id=1)` returns the core's own counters without error. Reset, start and stop with `neo_id=1` act on them too.

#### Desired behavior
`--counter=<id>` reads counter `<id>` for any id from 0 to 511, named or not, on every architecture. On Wormhole and Blackhole the library functions refuse NEO ids.

#### Acceptance criteria
- When `perf-counters read --block=FPU --counter=2` runs, then it prints counter 2's value in the same format as a named counter, with no "not found" warning.
- When `--counter` gives a named id or name, then the output is unchanged.
- When `--counter` gives an id outside 0..511, then the command reports that the id is out of range and reads no counter.
- When `read_perf_counters`, `reset_perf_counters`, `start_perf_counters` or `stop_perf_counters` gets a `neo_id` other than `None`, including 0, on Wormhole or Blackhole, then it raises `TTException`.
- When these functions get no `neo_id` on Wormhole or Blackhole, or a valid NEO id on Quasar, then they behave as before.

#### Scope
`perf-counters read --counter` on all architectures; library NEO handling on Wormhole and Blackhole. The CLI `--neo` keeps rejecting NEO ids there.

#### Verification
Tests on Wormhole n150 and n300 and Blackhole p150b, with NOC0 and NOC1. Quasar by simulator or board if available, otherwise by review.

</details>

<details>
<summary>Design: [lib] Read unnamed perf counter ids with --counter and reject NEO ids on Wormhole/Blackhole</summary>

#### Scope
- `perf-counters read --block=<b> --counter=<id>` reads counter `<id>` for any id from 0 to 511, whether the block's map names it or not, and prints the value as it does for a named counter.
- An id outside 0..511 prints `counter id <id> out of range (0..511)` and nothing is read.
- A counter given by name, or by a named id, prints what it printed before. An unknown name keeps the "not found" warning.
- On a block without NEOs (Wormhole, Blackhole), `read_perf_counters`, `reset_perf_counters`, `start_perf_counters` and `stop_perf_counters` raise `TTException` for any `neo_id` other than `None`, including 0.

Left alone: Quasar NEO handling, the CLI `--neo` check, and the signatures of the existing library functions.

#### API changes
- New public function, exported from `ttexalens`:

```python
def read_perf_counter(
    location: OnChipCoordinate,
    block_name: str,
    counter: int | str,
    *,
    noc_id: NocId | int | None = None,
    neo_id: int | None = None,
    safe_mode: bool | None = None,
) -> int
```

  It reads one counter by id (0..511, named or not) or by name. It raises `TTException` for an id out of range, an unknown name, or counters not available.
- `read_perf_counters`, `reset_perf_counters`, `start_perf_counters`, `stop_perf_counters`: signatures unchanged. With a `neo_id` on a block without NEOs they now raise `TTException("Performance counters are not available on <loc> (block_type=<type>, neo=<id>).")` instead of acting on the core's own counters. Their docstrings gain a note on `neo_id`.
- `list_perf_counters(location, neo_id=<id>)` on such a block returns `{}`.
- `NocBlock.get_perf_counters(neo_id)` returns `None` for a non-`None` `neo_id` unless the architecture's block overrides it, as `get_debug_bus` already does.
- `perf-counters read --counter`: behaviour as under Scope. The command's examples gain:

```
perf-counters read --block=FPU --counter=2      # Read a counter by id, also one without a name
perf-counters read --block=FPU --counter=600    # An id outside 0..511 is reported and not read
```

- `ttexalens.hardware.perf_counters._COUNTER_ID_LIMIT` becomes `COUNTER_ID_LIMIT`.

#### New modules and classes
- `ttexalens.perf_counters.read_perf_counter`: reads a single perf counter (see above).

The tests go into a new file, `test/ttexalens/unit_tests/test_perf_counters.py`.

</details>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
