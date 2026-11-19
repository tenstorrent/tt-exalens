# [hw] Fix duplicate BRISC icache flags and thread 1 cfg_space part names in Blackhole debug bus map

## Summary
The Blackhole Tensix debug bus map defines two BRISC signals twice and misnames the parts of a thread 1 signal. One of each duplicate pair is unreachable, and the thread 1 signal cannot be read by name.

## Current behavior
In `ttexalens/hardware/blackhole/functional_worker_debug_bus_signals.py`, one dict literal holds:

```
"brisc_icache_req_fifo_empty"  rd_sel=1 daisy_sel=7 sig_sel=26 mask=0x200   # tensix_icache_ctrl
"brisc_icache_req_fifo_full"   rd_sel=1 daisy_sel=7 sig_sel=26 mask=0x100   # tensix_icache_ctrl
"brisc_icache_req_fifo_full"   rd_sel=0 daisy_sel=7 sig_sel=1  mask=0x2     # brisc_group_c
"brisc_icache_req_fifo_empty"  rd_sel=0 daisy_sel=7 sig_sel=1  mask=0x1     # brisc_group_c

"tensix_frontend_t0_rq_head_rsrcs_target_cfg_space/0"    and ".../1"
"tensix_frontend_t1_rq_head_rsrcs_target_cfg_space_0_0"  rd_sel=2 mask=0x80000000
"tensix_frontend_t1_rq_head_rsrcs_target_cfg_space_2_1"  rd_sel=3 mask=0x3
"tensix_frontend_t2_rq_head_rsrcs_target_cfg_space/0"    and ".../1"
```

- The later entries win, so `tensix_icache_ctrl` has request-queue flags for TRISC0-2 but not BRISC.
- `debug-bus tensix_frontend_t1_rq_head_rsrcs_target_cfg_space` reports an unknown signal. For threads 0 and 2 it lists the parts.

## Desired behavior
Every signal name in the map is unique, and only names change. Existing BRISC names keep their current meaning, which matches Wormhole. The thread 1 signal splits into `/0` and `/1` like threads 0 and 2.

## Acceptance criteria
- When the map source is parsed for repeated keys, then none is found, and no signal's rd_sel, daisy_sel, sig_sel or mask differs from today.
- When `brisc_icache_req_fifo_empty` and `_full` are read on Blackhole, then they return the `brisc_group_c` bits (sig_sel 1, masks 0x1, 0x2).
- When group `tensix_icache_ctrl` is read on Blackhole, then it also has BRISC request-queue empty and full flags (sig_sel 26, masks 0x200, 0x100).
- When `debug-bus tensix_frontend_t1_rq_head_rsrcs_target_cfg_space` runs on Blackhole, then it lists `tensix_frontend_t1_rq_head_rsrcs_target_cfg_space/0` (rd_sel 2, mask 0x80000000) and `/1` (rd_sel 3, mask 0x3).
- When group `tensix_frontend_t1` is read, then it has one 3-bit signal `tensix_frontend_t1_rq_head_rsrcs_target_cfg_space`.

## Scope
The Blackhole Tensix debug bus signal map, through the debug bus library and the `debug-bus` command. Blackhole only.

## Verification
Device-free: a test that parses the map source and builds its groups and combined signals. Hardware: the command in the fourth criterion on a Blackhole board.
