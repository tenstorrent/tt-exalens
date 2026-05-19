# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""Quasar Tensix perf-counter block descriptions — TODO.

Quasar uses a different layout from Wormhole/Blackhole:

  - The classical PERF_CNT register block at +0x000..+0x03C / +0x0F0..+0x0F8
    is commented out in tt-metal/tt_metal/hw/inc/internal/tt-2xx/quasar/tensix.h.
  - PERF_CNT_MUX_CTRL has moved (offset 0x218 → 0x0F4 — see
    ttexalens/hardware/quasar/functional_neo_registers.py).
  - CFG-based per-TRISC start/stop slots (PERF_CNT_CMD0..3) replace the
    debug-bus block; see perf_counters.md §3 in the tensix RTL repo.
  - Multiple NEOs per worker → counters are per-NEO.

Phase 1 ships without a Quasar implementation. ``QuasarFunctionalWorkerBlock``
and the per-NEO blocks deliberately do not set ``perf_counters``, so
``noc_block.get_perf_counters(...)`` returns ``None`` and the public library
raises a clear error. Wire this in once the Quasar register map is
authoritatively documented.
"""

# Intentionally empty — see module docstring.
