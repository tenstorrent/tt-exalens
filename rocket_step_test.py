# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
"""Test single-step (QuasarRocketCoreDebug.step()) on a Quasar Rocket core.

No ebreak is used. We load a short sled of NOPs terminated by a self-loop, run
the core, halt it, point dpc at the start of the sled, and then single-step,
checking that the PC advances by exactly one instruction (4 bytes) each time.

The vcs-quasar-2x3 sim self-terminates (RTL $finish) at ~13.6us sim time, which
is a fixed ~280s of real wall-clock after "waiting for host". So this must run
right after the sim is ready and stay lean; each line is timestamped so we can
see how much wall-clock each debug transaction costs.

    python3 rocket_step_test.py [num_steps]   # default 2
"""
import os
import sys
import struct
import threading
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ttexalens  # noqa: E402
from ttexalens.tt_exalens_init import init_ttexalens_remote  # noqa: E402

NOP = 0x00000013  # addi x0, x0, 0
JAL_SELF = 0x0000006F  # jal x0, 0  (spin in place)

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


def main():
    num_steps = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    start_watchdog(270)

    log(f"ttexalens: {ttexalens.__file__}")
    ctx = init_ttexalens_remote(port=5556, safe_mode=False)
    device, loc = wait_for_device(ctx)
    risc = device.get_block(loc).get_risc_debug("rocket0")
    log(f"connected, rocket0 @ {loc}")

    results = []
    risc.ensure_debug_module_is_active()
    # num_steps NOPs then a self-loop; stepping walks NOP@0, NOP@4, ... up to
    # the self-loop (which lands at num_steps*4 = the final expected PC).
    words = [NOP] * num_steps + [JAL_SELF]
    sled = b"".join(struct.pack("<I", w) for w in words)
    # Load via SBA (system bus): on this sim the hart fetches SBA-written
    # memory, whereas NoC writes to 0x0 are not fetched by the core.
    log(f"loading {len(words)} words to 0x0 via SBA")
    risc.set_reset_signal(True)
    for i, word in enumerate(words):
        risc.write_memory(i * 4, word)
    risc.set_code_start_address(0x0)
    risc.set_reset_signal(False)
    log("released core from reset")

    risc.halt()
    log("halted")

    risc.write_gpr(32, 0x0)  # dpc <- 0  (redirect PC to start, no ebreak)
    log("dpc<-0 (start PC); stepping (the step PCs below imply start==0)")

    for i in range(num_steps):
        expected = (i + 1) * 4
        risc.step()
        pc = risc.get_pc()
        log(f"step {i + 1}: get_pc()=0x{pc:x} (expect 0x{expected:x}) {'OK' if pc == expected else 'MISMATCH'}")
        results.append((f"step{i + 1}", pc, expected))

    passed = all(got == exp for _, got, exp in results)
    log("==== SUMMARY ====")
    for name, got, exp in results:
        log(f"  {name:8s} got=0x{got:<6x} exp=0x{exp:<6x} {'PASS' if got == exp else 'FAIL'}")
    log(f"==== {'ALL PASS' if passed else 'FAILED'} ====")
    return 0 if passed else 1


if __name__ == "__main__":
    try:
        rc = main()
    except Exception:
        log("EXCEPTION:\n" + traceback.format_exc())
        rc = 1
    os._exit(rc)
