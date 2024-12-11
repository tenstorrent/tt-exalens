# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttlens import tt_util as util

import os
import signal
import subprocess
import time


def start_server(port: int, wanted_devices: "List[int]" = None, init_jtag=False) -> subprocess.Popen:
    if util.is_port_available(int(port)):
        ttlens_server = spawn_standalone_ttlens_stub(port, wanted_devices, init_jtag)
        if ttlens_server is None:
            raise util.TTFatalException("Could not start ttlens-server.")
        return ttlens_server

    raise util.TTFatalException(f"Port {port} not available. A TTLens server might alreasdy be running.")


def spawn_standalone_ttlens_stub(port: int, wanted_devices: "List[int]" = None, init_jtag=False) -> subprocess.Popen:
    print("Spawning ttlens-server...")

    ttlens_server_standalone = "/ttlens-server-standalone"
    if "BUDA_HOME" not in os.environ:
        os.environ["BUDA_HOME"] = os.path.abspath(util.application_path() + "/../")
    ttlens_server_standalone = f"/../build/bin{ttlens_server_standalone}"

    ttlens_stub_path = os.path.abspath(util.application_path() + ttlens_server_standalone)
    library_path = os.path.abspath(os.path.dirname(ttlens_stub_path))
    ld_lib_path = os.environ.get("LD_LIBRARY_PATH", "")
    os.environ["LD_LIBRARY_PATH"] = library_path + ":" + ld_lib_path if ld_lib_path else library_path

    try:
        ttlens_stub_args = [f"{port}"]

        if wanted_devices:
            ttlens_stub_args += ["-d"] + [str(d) for d in wanted_devices]

        if init_jtag:
            ttlens_stub_args += ["--jtag"]

        ttlens_stub = subprocess.Popen(
            [ttlens_stub_path] + ttlens_stub_args,
            preexec_fn=os.setsid,
            stdin=subprocess.PIPE,  # We close by sending SIGTERM
            env=os.environ.copy(),
        )
    except:
        if os.path.islink(ttlens_stub_path):
            if not os.path.exists(os.readlink(ttlens_stub_path)):
                util.FATAL(f"Missing ttlens-server-standalone. Try: make build")
        raise

    util.INFO("ttlens-server started.")
    return ttlens_stub


# Terminates ttlens-server spawned in connect_to_server
def stop_server(ttlens_stub: subprocess.Popen):
    if ttlens_stub is not None and ttlens_stub.poll() is None:
        os.killpg(os.getpgid(ttlens_stub.pid), signal.SIGTERM)
        time.sleep(0.1)
        if ttlens_stub.poll() is None:
            util.VERBOSE("ttlens-server did not respond to SIGTERM. Sending SIGKILL...")
            os.killpg(os.getpgid(ttlens_stub.pid), signal.SIGKILL)

        time.sleep(0.1)
        if ttlens_stub.poll() is None:
            util.ERROR(
                f"ttlens-server did not respond to SIGKILL. The process {ttlens_stub.pid} is still running. Please kill it manually."
            )
        else:
            util.INFO("ttlens-server terminated.")
