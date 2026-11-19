# Fix duplicate BRISC icache flags and thread 1 cfg_space part names in the Blackhole debug bus map

The Blackhole Tensix debug bus map defined `brisc_icache_req_fifo_empty` and `_full` twice. The `brisc_group_c` pair (sig_sel 1) replaced the icache controller pair (sig_sel 26), so `tensix_icache_ctrl` had no BRISC flags. The icache controller pair is now `brisc_icache_ctrl_req_fifo_empty/full`. `brisc_icache_req_fifo_*` keeps its current meaning, the same as on Wormhole.

The thread 1 `rq_head_rsrcs_target_cfg_space` parts were named `_0_0` and `_2_1`, so they were not joined into one signal, and `debug-bus tensix_frontend_t1_rq_head_rsrcs_target_cfg_space` reported an unknown signal. They are now `/0` and `/1`, like threads 0 and 2. No signal's selectors or masks change.

A new device-free test class checks the map source for repeated keys and checks the renamed signals.

## Verification
pre-commit, mypy and basedpyright pass.
**Hardware:** Wormhole: not tested, the machine did not answer. Blackhole: not tested, no reservation.
**Not verified:** the new tests have not run; the Blackhole device test and the `debug-bus` command on Blackhole; tt-metal use of the removed `_0_0` and `_2_1` names.

Closes #1286

<details>
<summary>Issue: [hw] Fix duplicate BRISC icache flags and thread 1 cfg_space part names in Blackhole debug bus map</summary>

#### Summary
The Blackhole Tensix debug bus map defines two BRISC signals twice and misnames the parts of a thread 1 signal. One of each duplicate pair is unreachable, and the thread 1 signal cannot be read by name.

#### Current behavior
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

#### Desired behavior
Every signal name in the map is unique, and only names change. Existing BRISC names keep their current meaning, which matches Wormhole. The thread 1 signal splits into `/0` and `/1` like threads 0 and 2.

#### Acceptance criteria
- When the map source is parsed for repeated keys, then none is found, and no signal's rd_sel, daisy_sel, sig_sel or mask differs from today.
- When `brisc_icache_req_fifo_empty` and `_full` are read on Blackhole, then they return the `brisc_group_c` bits (sig_sel 1, masks 0x1, 0x2).
- When group `tensix_icache_ctrl` is read on Blackhole, then it also has BRISC request-queue empty and full flags (sig_sel 26, masks 0x200, 0x100).
- When `debug-bus tensix_frontend_t1_rq_head_rsrcs_target_cfg_space` runs on Blackhole, then it lists `tensix_frontend_t1_rq_head_rsrcs_target_cfg_space/0` (rd_sel 2, mask 0x80000000) and `/1` (rd_sel 3, mask 0x3).
- When group `tensix_frontend_t1` is read, then it has one 3-bit signal `tensix_frontend_t1_rq_head_rsrcs_target_cfg_space`.

#### Scope
The Blackhole Tensix debug bus signal map, through the debug bus library and the `debug-bus` command. Blackhole only.

#### Verification
Device-free: a test that parses the map source and builds its groups and combined signals. Hardware: the command in the fourth criterion on a Blackhole board.

</details>

<details>
<summary>Design: Fix duplicate BRISC icache flags and thread 1 cfg_space part names in Blackhole debug bus map</summary>

#### Scope
- Every key in the Blackhole Tensix debug bus signal map is unique. Four key names change; no `rd_sel`, `daisy_sel`, `sig_sel` or `mask` changes.
- `brisc_icache_req_fifo_empty` and `_full` keep today's meaning (group `brisc_group_c`, `sig_sel` 1), as on Wormhole.
- The BRISC request-queue flags of the icache controller get new names, so group `tensix_icache_ctrl` has them for BRISC as it has for TRISC0-2.
- The thread 1 `rq_head_rsrcs_target_cfg_space` signal is split into `/0` and `/1` like threads 0 and 2: `debug-bus` lists its parts, and group `tensix_frontend_t1` holds it as one 3-bit signal.
- A device-free test parses the map source for repeated keys.

Left alone: the Wormhole and Quasar maps, the debug bus store, the `debug-bus` command, and other split signals with old part names.

#### API changes
Signal names in `ttexalens/hardware/blackhole/functional_worker_debug_bus_signals.py`:

| Old name | New name | Location |
|---|---|---|
| `brisc_icache_req_fifo_empty` (first, shadowed entry) | `brisc_icache_ctrl_req_fifo_empty` | rd_sel 1, sig_sel 26, mask 0x200 |
| `brisc_icache_req_fifo_full` (first, shadowed entry) | `brisc_icache_ctrl_req_fifo_full` | rd_sel 1, sig_sel 26, mask 0x100 |
| `tensix_frontend_t1_rq_head_rsrcs_target_cfg_space_0_0` | `tensix_frontend_t1_rq_head_rsrcs_target_cfg_space/0` | rd_sel 2, sig_sel 8, mask 0x80000000 |
| `tensix_frontend_t1_rq_head_rsrcs_target_cfg_space_2_1` | `tensix_frontend_t1_rq_head_rsrcs_target_cfg_space/1` | rd_sel 3, sig_sel 8, mask 0x3 |

The `_0_0` / `_2_1` names stop existing. The `brisc_icache_ctrl_req_fifo_*` names are new: nothing could read those bits by name before.

No function signature, command syntax or docstring changes.

#### New modules and classes
None in product code. The tests gain one device-free class, `TestBlackholeDebugBusSignalMap`, in the existing `test/ttexalens/unit_tests/test_debug_bus.py`.

#### Open questions
- The new names keep `brisc_icache_req_fifo_*` compatible. The alternative follows the TRISC pattern: the `tensix_icache_ctrl` pair takes the plain name and the `brisc_group_c` pair is renamed, which changes what the existing name returns on Blackhole.

</details>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
