<!--
SPDX-FileCopyrightText: (c) 2026 Tenstorrent AI ULC
SPDX-License-Identifier: Apache-2.0
-->
# Rocket callstack test

Recreated because **no test confirming Rocket `get_callstack()` works has ever
existed** — not in the worktree, not on any local or `origin/*` branch, not
anywhere in git history. The closest artifact,
`rocket_pattern_demo/rocket_write_pattern_demo.py:133`, calls `lib.callstack()`
but only *prints* the result, so a 0- or 1-frame answer read as success.

For **step**, a real test already existed and ships alongside this one as
`rocket_step_test.py` in the repo root. It has a genuine oracle (asserts the PC
advances exactly 4 bytes per `step()`), but it had never been committed to any
branch and has no saved run output, so `step()` is implemented-but-unproven:
PR #1129 landed it on `main` with zero tests.

## Files

| File | Needs a device? | Purpose |
|---|---|---|
| `main.cc`, `crt0.S`, `link.ld`, `build.sh` | no | 4-frame test program (`main → f3 → f2 → f1`, f1 spins) |
| `build_in_docker.sh` | no | runs `build.sh` in the Ubuntu 22.04 image (sfpi needs glibc ≥ 2.33; RHEL8 host has 2.28) |
| `test_callstack_offline.py` | **no** | proves the ELF/DWARF/unwinder produce 4 frames, using a synthetic stack + the driver preflight |
| `rocket_callstack_test.py` | yes (sim) | the real test: SBA-load, run, halt in f1, `lib.callstack()`, **assert 4 frames** |
| `quasar_rocket_callstack_prereq.patch` | — | the driver overrides the test needs; **not applied** |

Rebuilding is **optional** — `callstack_test.elf` / `.bin` are committed so both
tests run as-is. `build.sh` additionally needs the sfpi toolchain at
`build_riscv/sfpi/` (a gitignored local build tree; `./scripts/create-venv.sh`
or the usual riscv build populates it) and, on a RHEL8 host, Docker.

`crt0.S` and `link.ld` were recovered from reverted commit `8a9a2d7`
(`git show 8a9a2d7:rocket_pattern_demo/crt0.S`). `link.ld`'s `//` SPDX comments
are a linker-script syntax error — the fix was sitting unapplied in `stash@{0}`
and is folded in here.

## Run order

```bash
./rocket_callstack_test/build_in_docker.sh              # build + offline DWARF gate
.venv/bin/python rocket_callstack_test/test_callstack_offline.py   # no device needed
# then, with a sim server on 5556:
.venv/bin/python rocket_callstack_test/rocket_callstack_test.py 2>&1 | tee callstack_run.log
```

Always `tee` the log. The absence of any saved output is the single reason none
of the earlier Rocket debug work counts as evidence today.

## Why the depth assertion is load-bearing

`MemoryAccess::try_read_word` (`ttexalens/cpp/elf/memory_access.hpp:31`) wraps
every stack read in `catch (...) { return std::nullopt; }`, and
`ttexalens/cpp/elf/callstack.cpp:472` turns a missing return address into
`break`. **A broken memory path yields a short callstack, never an exception.**
A 1-frame result is indistinguishable from success unless depth is asserted —
which is exactly why the old demo's print loop proved nothing.

## The blocker

`lib.callstack` builds a `RiscDebugMemoryAccess` with `restricted_access=True`.
Each stack read goes `read()` → `_validate_access()` → `risc_debug.get_l1()`,
and `read()` also enters `risc_debug.ensure_private_memory_access()`.
`QuasarRocketCoreDebug` overrides **neither** (nor `can_debug` /
`get_data_private_memory`), so both hit `raise NotImplementedError` in the
abstract `RocketCoreDebug`. `try_read_word` swallows it → frame 0 only.

`test_callstack_offline.py` reports this with no hardware. To fix:

```bash
git apply rocket_callstack_test/quasar_rocket_callstack_prereq.patch
```

It mirrors `BabyRiscDebug` (`ttexalens/hardware/baby_risc_debug.py:790-800`,
`:597-603`). `rocket0`'s `l1` is the 4 MB block at private `0x0`
(`quasar/functional_worker_block.py:23`) and `crt0.S` sets `sp = 0x40000`, so
every stack address is inside L1 and `restricted_access=True` is satisfied.

## Facts worth keeping

- **The CFA at the spin PC comes from `s0`, not `sp`.** At `-O0` GCC keeps a
  frame pointer, so the FDE rule is `DW_CFA_def_cfa: r8 (s0) ofs 0`
  (`callstack_test.frames`). The driver must serve `read_gpr(8)`; serving only
  `sp` yields `cfa=0x0` and one frame. Verified — it is what the first offline
  run got wrong.
- **Load over SBA, never the NoC.** `write_memory_bytes()` on the Rocket debug
  object goes through the debug module's system bus; the hart does not reliably
  fetch NoC-written TL1 `0x0`.
- **Do not use `ebreak` to stop the core.** `dcsr.ebreakm` is 0 out of reset, so
  an M-mode `ebreak` traps to `mtvec` (=0) and re-runs `crt0`. The program spins
  instead and the host calls `halt()`.
- **`halt()` is single-shot and racy on the sim.**
  `quasar/rocket_core_debug.py:103` writes HALTREQ, drops it, checks
  `is_halted()` once, then raises `RiscHaltError`. Both tests poll around it
  (`poll_halt()`); a polling `halt()` was noted as needed but never committed.
- **Pre-halt before `lib.callstack`** so its `ensure_halted()` sees
  `was_halted=True` and does not `cont()` the core on the way out.
- **`is_ebreak_hit` is already bypassed** for Rocket in `tt_exalens_lib.py:653`
  (`origin/adjordjevic/fix_callstack` landed), so that is no longer a blocker.
- The historical `~13.6 us` / `~278 s` RTL `$finish` timebomb may be gone on the
  current sim tag (two runs on 2026-09-01 reached 20.7 us and 37.4 us). Verify
  before budgeting transactions; both tests keep a watchdog regardless.
