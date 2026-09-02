# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
"""On-simulator test that get_callstack() unwinds a Quasar Rocket core.

This is the test that did not exist. rocket_pattern_demo/rocket_write_pattern_demo.py
called lib.callstack() but only *printed* the result, so a zero- or one-frame
answer read as success; nothing ever asserted the depth.

What it does:
  1. loads callstack_test.elf's flat image to TL1 0x0 over the debug-module
     SYSTEM BUS (SBA). NoC writes to 0x0 are not reliably fetched by the hart
     on this sim -- use write_memory_bytes(), never the NoC path.
  2. releases reset and lets the core run into f1's spin loop, four frames deep
     (main -> f3 -> f2 -> f1).
  3. halts, confirms the PC is inside f1, then calls lib.callstack().
  4. ASSERTS 4 frames named f1, f2, f3, main.

Step 4 is the whole point. MemoryAccess::try_read_word
(ttexalens/cpp/elf/memory_access.hpp:31) wraps every stack read in
`catch (...) { return nullopt; }`, and callstack.cpp:472 turns a missing return
address into `break`. A broken memory path therefore yields a SHORT callstack,
never an exception -- so depth must be asserted or the test proves nothing.

Prerequisites:
  * build the ELF:  ./build_in_docker.sh      (writes callstack_test.elf/.bin)
  * validate offline first: python3 test_callstack_offline.py
  * a tt-exalens server on port 5556 fronting the vcs-quasar-2x3 sim:
      tail -f /dev/null | NNG_SOCKET_LOCAL_PORT=5555 \
        python3 tt-exalens.py --server --port=5556 \
        -s ../tt-umd-simulators/build/vcs-quasar-2x3/ > server.log 2>&1 &
    NNG_SOCKET_ADDR must be UNSET, and the `tail -f /dev/null |` prefix is
    required (--server busy-loops on EOF from /dev/null stdin and starves the
    request handler).
  * historically the sim self-terminated (RTL $finish) ~278s of wall clock after
    "waiting for host", so start this immediately and keep it lean. Every line
    is timestamped to show what each debug transaction costs. The watchdog below
    is the backstop.

    python3 rocket_callstack_test/rocket_callstack_test.py

Exit code 0 = pass. Save the output -- the absence of a saved log is the reason
none of the earlier Rocket debug work counts as evidence:
    python3 rocket_callstack_test/rocket_callstack_test.py 2>&1 | tee callstack_run.log
"""
import os
import sys
import threading
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import ttexalens  # noqa: E402
import ttexalens.tt_exalens_lib as lib  # noqa: E402
from ttexalens.tt_exalens_init import init_ttexalens_remote  # noqa: E402
from test_callstack_offline import report_driver_overrides  # noqa: E402

ELF_PATH = os.path.join(HERE, "callstack_test.elf")
BIN_PATH = os.path.join(HERE, "callstack_test.bin")

LOAD_ADDR = 0x0
F1_RANGE = (0x24, 0x38)  # [start, end) of f1 in callstack_test.elf
SPIN_PC = 0x34  # the `j .` inside f1
EXPECTED_FRAMES = ["f1", "f2", "f3", "main"]
WATCHDOG_SECONDS = 270

_t0 = time.time()


def log(*a):
    print(f"[{time.time() - _t0:6.1f}s]", *a, flush=True)


def start_watchdog(seconds: int):
    def bomb():
        time.sleep(seconds)
        log(f"!!! WATCHDOG {seconds}s -> os._exit(2) (sim likely dead/wedged)")
        os._exit(2)

    threading.Thread(target=bomb, daemon=True).start()


def wait_for_device(ctx, timeout=60):
    start = time.time()
    while True:
        try:
            device = ctx.devices[0]
            locs = device.get_block_locations(block_type="functional_workers")
            if locs:
                return device, locs[0]
        except (KeyError, IndexError):
            pass
        if time.time() - start > timeout:
            raise TimeoutError("Device did not enumerate in time")
        time.sleep(0.2)


def poll_halt(risc, attempts=50):
    """Halt the core, tolerating QuasarRocketCoreDebug.halt()'s single-shot check.

    halt() (ttexalens/hardware/quasar/rocket_core_debug.py:103) writes HALTREQ,
    drops it, then checks is_halted() exactly once and raises RiscHaltError if
    the hart has not stopped yet. On the simulator that check is racy, so retry.
    """
    from ttexalens.exceptions import RiscHaltError

    for i in range(attempts):
        if risc.is_halted():
            return True
        try:
            risc.halt()
        except RiscHaltError:
            pass
        if i and i % 10 == 0:
            log(f"  ...still trying to halt ({i} attempts)")
    return risc.is_halted()


def main() -> int:
    start_watchdog(WATCHDOG_SECONDS)
    log(f"ttexalens: {ttexalens.__file__}")

    for path in (ELF_PATH, BIN_PATH):
        if not os.path.exists(path):
            log(f"FAIL: {path} missing -- run ./build_in_docker.sh first")
            return 1
    with open(BIN_PATH, "rb") as f:
        code = f.read()
    log(f"code image: {len(code)} bytes ({len(code) // 4} words)")

    # Cheap, hardware-free check of the known blocker. Report but do not bail --
    # if it has been fixed we want the real run, and if not we want the sim
    # evidence of the truncation.
    driver_ok = report_driver_overrides()

    ctx = init_ttexalens_remote(port=5556, safe_mode=False)
    device, loc = wait_for_device(ctx)
    risc = device.get_block(loc).get_risc_debug("rocket0")
    log(f"connected, rocket0 @ {loc}")

    risc.set_reset_signal(True)
    assert risc.is_in_reset(), "core did not enter reset"
    risc.take_debug_module_out_of_reset()
    risc.ensure_debug_module_is_active()
    log("core in reset, debug module active")

    log(f"loading {len(code)} bytes to 0x{LOAD_ADDR:x} via SBA (system bus)")
    risc.write_memory_bytes(LOAD_ADDR, code)
    # Spot-check the tail so a silently-dropped burst cannot masquerade as a
    # callstack bug later.
    tail_off = (len(code) // 4 - 1) * 4
    expected_tail = int.from_bytes(code[tail_off : tail_off + 4], "little")
    actual_tail = risc.read_memory(LOAD_ADDR + tail_off)
    assert (
        actual_tail == expected_tail
    ), f"SBA load verify failed at 0x{LOAD_ADDR + tail_off:x}: got 0x{actual_tail:08x}, want 0x{expected_tail:08x}"
    log(f"load verified (tail word 0x{actual_tail:08x} @ 0x{LOAD_ADDR + tail_off:x})")

    risc.set_code_start_address(LOAD_ADDR)
    risc.set_reset_signal(False)
    assert not risc.is_in_reset(), "core did not leave reset"
    log("released core from reset; it should run crt0 -> main -> f3 -> f2 -> f1 and spin")

    # Halt, and make sure we landed in f1 rather than still in crt0's bss loop.
    # Pre-halting here also makes lib.callstack's ensure_halted() a no-op, so it
    # will not cont() the core out from under us on exit.
    pc = None
    for attempt in range(10):
        if not poll_halt(risc):
            log(f"  attempt {attempt}: could not halt")
            continue
        pc = risc.read_gpr(32)  # index 32 -> get_pc() -> dpc via progbuf
        log(f"  attempt {attempt}: halted at pc=0x{pc:x}")
        if F1_RANGE[0] <= pc < F1_RANGE[1]:
            break
        risc.cont()  # not deep enough yet; let it run on
    assert pc is not None, "never managed to halt the core"
    assert F1_RANGE[0] <= pc < F1_RANGE[1], (
        f"halted at pc=0x{pc:x}, outside f1 [0x{F1_RANGE[0]:x},0x{F1_RANGE[1]:x}) -- "
        f"the core never reached the 4-deep spin loop, so the callstack below would be meaningless"
    )
    sp = risc.read_gpr(2)
    s0 = risc.read_gpr(8)  # CFA register at -O0; get_callstack needs this one
    log(f"halted in f1: pc=0x{pc:x} sp=0x{sp:x} s0=0x{s0:x}")

    cs = lib.callstack(loc, ELF_PATH, 0, "rocket0", context=ctx, extract_variables=False)

    log(f"callstack ({len(cs)} frames):")
    for i, frame in enumerate(cs):
        frame_pc = "?" if frame.pc is None else f"0x{frame.pc:08x}"
        fi = frame.file_info
        where = f"{os.path.basename(fi.file)}:{fi.line}" if fi else "?"
        log(f"  #{i} {frame_pc} in {frame.function_name} at {where}")

    names = [f.function_name for f in cs]
    failures = []
    if len(cs) < len(EXPECTED_FRAMES):
        detail = f"callstack truncated to {len(cs)} frame(s), expected {len(EXPECTED_FRAMES)}"
        if not driver_ok:
            detail += " -- driver preflight already flagged the missing overrides above"
        failures.append(detail)
    if names[: len(EXPECTED_FRAMES)] != EXPECTED_FRAMES:
        failures.append(f"frame names {names[: len(EXPECTED_FRAMES)]}, expected {EXPECTED_FRAMES}")
    if cs and cs[0].pc != pc:
        failures.append(f"frame #0 pc=0x{cs[0].pc:x} does not match read_gpr(32)=0x{pc:x}")
    if cs and (cs[0].file_info is None or not cs[0].file_info.file.endswith("main.cc")):
        failures.append(f"frame #0 file={cs[0].file_info and cs[0].file_info.file}, expected .../main.cc")

    log("==== SUMMARY ====")
    log(f"  frames        : {len(cs)} (want {len(EXPECTED_FRAMES)})")
    log(f"  names         : {names}")
    log(f"  halted pc     : 0x{pc:x} (spin loop is 0x{SPIN_PC:x})")
    if failures:
        for f in failures:
            log(f"  FAIL: {f}")
        log("==== FAILED ====")
        return 1
    log("==== ALL PASS ====")
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception:
        log("EXCEPTION:\n" + traceback.format_exc())
        rc = 1
    os._exit(rc)
