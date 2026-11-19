# Design: [lib] Read unnamed perf counter ids with --counter and reject NEO ids on Wormhole/Blackhole

## Scope
- `perf-counters read --block=<b> --counter=<id>` reads counter `<id>` for any id from 0 to 511, whether the block's map names it or not, and prints the value as it does for a named counter.
- An id outside 0..511 prints `counter id <id> out of range (0..511)` and nothing is read.
- A counter given by name, or by a named id, prints what it printed before. An unknown name keeps the "not found" warning.
- On a block without NEOs (Wormhole, Blackhole), `read_perf_counters`, `reset_perf_counters`, `start_perf_counters` and `stop_perf_counters` raise `TTException` for any `neo_id` other than `None`, including 0.

Left alone: Quasar NEO handling, the CLI `--neo` check, and the signatures of the existing library functions.

## API changes
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

## New modules and classes
- `ttexalens.perf_counters.read_perf_counter`: reads a single perf counter (see above).

The tests go into a new file, `test/ttexalens/unit_tests/test_perf_counters.py`.
