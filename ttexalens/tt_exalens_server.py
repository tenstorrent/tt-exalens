# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from typing import List
from ttexalens import util as util

import os
import signal
import subprocess
import time


def start_server(
    port: int,
    wanted_devices: "List[int]" = None,
    init_jtag=False,
    use_noc1=False,
    simulation_directory: str = None,
    background=False,
) -> subprocess.Popen:
    if util.is_port_available(int(port)):
        ttexalens_server = spawn_standalone_ttexalens_stub(
            port, wanted_devices, init_jtag, use_noc1, simulation_directory, background
        )
        if ttexalens_server is None:
            raise util.TTFatalException("Could not start ttexalens-server.")
        return ttexalens_server

    raise util.TTFatalException(f"Port {port} not available. A TTExaLens server might alreasdy be running.")


def spawn_standalone_ttexalens_stub(
    port: int,
    wanted_devices: "List[int]" = None,
    init_jtag=False,
    use_noc1=False,
    simulation_directory: str = None,
    background=False,
) -> subprocess.Popen:
    print("Spawning ttexalens-server...")

    ttexalens_server_standalone = "/ttexalens-server-standalone"
    if "BUDA_HOME" not in os.environ:
        os.environ["BUDA_HOME"] = os.path.abspath(util.application_path() + "/../")
    ttexalens_server_standalone = f"/../build/bin{ttexalens_server_standalone}"

    ttexalens_stub_path = os.path.abspath(util.application_path() + ttexalens_server_standalone)
    library_path = os.path.abspath(os.path.dirname(ttexalens_stub_path))
    ld_lib_path = os.environ.get("LD_LIBRARY_PATH", "")
    os.environ["LD_LIBRARY_PATH"] = library_path + ":" + ld_lib_path if ld_lib_path else library_path

    try:
        ttexalens_stub_args = [f"{port}"]

        if wanted_devices:
            ttexalens_stub_args += ["-d"] + [str(d) for d in wanted_devices]

        if init_jtag:
            ttexalens_stub_args += ["--jtag"]

        if use_noc1:
            ttexalens_stub_args += ["--use-noc1"]

        if background:
            ttexalens_stub_args += ["--background"]

        if simulation_directory:
            ttexalens_stub_args += ["-s", simulation_directory]

        ttexalens_stub = subprocess.Popen(
            [ttexalens_stub_path] + ttexalens_stub_args,
            preexec_fn=os.setsid,
            stdin=subprocess.PIPE,  # We close by sending SIGTERM
            env=os.environ.copy(),
        )
    except:
        if os.path.islink(ttexalens_stub_path):
            if not os.path.exists(os.readlink(ttexalens_stub_path)):
                util.FATAL(f"Missing ttexalens-server-standalone. Try: make build")
        raise

    util.INFO("ttexalens-server started.")
    return ttexalens_stub


# Terminates ttexalens-server spawned in connect_to_server
def stop_server(ttexalens_stub: subprocess.Popen):
    if ttexalens_stub is not None and ttexalens_stub.poll() is None:
        os.killpg(os.getpgid(ttexalens_stub.pid), signal.SIGTERM)
        time.sleep(0.1)
        if ttexalens_stub.poll() is None:
            util.VERBOSE("ttexalens-server did not respond to SIGTERM. Sending SIGKILL...")
            os.killpg(os.getpgid(ttexalens_stub.pid), signal.SIGKILL)

        time.sleep(0.1)
        if ttexalens_stub.poll() is None:
            util.ERROR(
                f"ttexalens-server did not respond to SIGKILL. The process {ttexalens_stub.pid} is still running. Please kill it manually."
            )
        else:
            util.INFO("ttexalens-server terminated.")
