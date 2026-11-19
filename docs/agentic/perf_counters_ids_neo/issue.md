# [lib] Read unnamed perf counter ids with --counter and reject NEO ids on Wormhole/Blackhole

## Summary
`perf-counters read --counter` cannot read counter ids missing from the block's name map, although usage allows 0 to 511. On Wormhole and Blackhole, the perf-counter library functions silently accept a NEO id.

## Current behavior
FPU names only ids 0, 1 and 257, so counter 2 is never read:

```
perf-counters read --block=FPU --counter=2
counter 2 not found in block FPU
```

On Wormhole and Blackhole, which have no NEOs, `read_perf_counters(loc, neo_id=1)` returns the core's own counters without error. Reset, start and stop with `neo_id=1` act on them too.

## Desired behavior
`--counter=<id>` reads counter `<id>` for any id from 0 to 511, named or not, on every architecture. On Wormhole and Blackhole the library functions refuse NEO ids.

## Acceptance criteria
- When `perf-counters read --block=FPU --counter=2` runs, then it prints counter 2's value in the same format as a named counter, with no "not found" warning.
- When `--counter` gives a named id or name, then the output is unchanged.
- When `--counter` gives an id outside 0..511, then the command reports that the id is out of range and reads no counter.
- When `read_perf_counters`, `reset_perf_counters`, `start_perf_counters` or `stop_perf_counters` gets a `neo_id` other than `None`, including 0, on Wormhole or Blackhole, then it raises `TTException`.
- When these functions get no `neo_id` on Wormhole or Blackhole, or a valid NEO id on Quasar, then they behave as before.

## Scope
`perf-counters read --counter` on all architectures; library NEO handling on Wormhole and Blackhole. The CLI `--neo` keeps rejecting NEO ids there.

## Verification
Tests on Wormhole n150 and n300 and Blackhole p150b, with NOC0 and NOC1. Quasar by simulator or board if available, otherwise by review.
