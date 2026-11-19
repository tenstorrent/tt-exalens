# Design: Fix duplicate BRISC icache flags and thread 1 cfg_space part names in Blackhole debug bus map

## Scope
- Every key in the Blackhole Tensix debug bus signal map is unique. Four key names change; no `rd_sel`, `daisy_sel`, `sig_sel` or `mask` changes.
- `brisc_icache_req_fifo_empty` and `_full` keep today's meaning (group `brisc_group_c`, `sig_sel` 1), as on Wormhole.
- The BRISC request-queue flags of the icache controller get new names, so group `tensix_icache_ctrl` has them for BRISC as it has for TRISC0-2.
- The thread 1 `rq_head_rsrcs_target_cfg_space` signal is split into `/0` and `/1` like threads 0 and 2: `debug-bus` lists its parts, and group `tensix_frontend_t1` holds it as one 3-bit signal.
- A device-free test parses the map source for repeated keys.

Left alone: the Wormhole and Quasar maps, the debug bus store, the `debug-bus` command, and other split signals with old part names.

## API changes
Signal names in `ttexalens/hardware/blackhole/functional_worker_debug_bus_signals.py`:

| Old name | New name | Location |
|---|---|---|
| `brisc_icache_req_fifo_empty` (first, shadowed entry) | `brisc_icache_ctrl_req_fifo_empty` | rd_sel 1, sig_sel 26, mask 0x200 |
| `brisc_icache_req_fifo_full` (first, shadowed entry) | `brisc_icache_ctrl_req_fifo_full` | rd_sel 1, sig_sel 26, mask 0x100 |
| `tensix_frontend_t1_rq_head_rsrcs_target_cfg_space_0_0` | `tensix_frontend_t1_rq_head_rsrcs_target_cfg_space/0` | rd_sel 2, sig_sel 8, mask 0x80000000 |
| `tensix_frontend_t1_rq_head_rsrcs_target_cfg_space_2_1` | `tensix_frontend_t1_rq_head_rsrcs_target_cfg_space/1` | rd_sel 3, sig_sel 8, mask 0x3 |

The `_0_0` / `_2_1` names stop existing. The `brisc_icache_ctrl_req_fifo_*` names are new: nothing could read those bits by name before.

No function signature, command syntax or docstring changes.

## New modules and classes
None in product code. The tests gain one device-free class, `TestBlackholeDebugBusSignalMap`, in the existing `test/ttexalens/unit_tests/test_debug_bus.py`.

## Open questions
- The new names keep `brisc_icache_req_fifo_*` compatible. The alternative follows the TRISC pattern: the `tensix_icache_ctrl` pair takes the plain name and the `brisc_group_c` pair is renamed, which changes what the existing name returns on Blackhole.
