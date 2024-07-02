# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import tt_util as util

import os
import signal
import subprocess
import time

def start_server(port: int, runtime_data_yaml_filename: str, run_dirpath: str = None, wanted_devices: "list[int]" = None) -> subprocess.Popen:
    if util.is_port_available(int(port)):
        debuda_server = spawn_standalone_debuda_stub(port, runtime_data_yaml_filename, run_dirpath, wanted_devices)
        if debuda_server is None:
            raise util.TTFatalException("Could not start debuda-server.")
        return debuda_server
    
    raise util.TTFatalException(f"Port {port} not available. A debuda server might alreasdy be running.")

# The server needs the runtime_data.yaml to get the netlist path, arch, and device
def spawn_standalone_debuda_stub(port: int, runtime_data_yaml_filename: str, run_dirpath: str,  wanted_devices: "list[int]" = None) -> subprocess.Popen:
    print("Spawning debuda-server...")

    debuda_server_standalone = "/debuda-server-standalone"
    if "BUDA_HOME" not in os.environ:
        os.environ["BUDA_HOME"] = os.path.abspath(util.application_path() + "/../")
    debuda_server_standalone = f"/../build/bin{debuda_server_standalone}"

    debuda_stub_path = os.path.abspath(
        util.application_path() + debuda_server_standalone
    )
    library_path = os.path.abspath(os.path.dirname(debuda_stub_path))
    ld_lib_path = os.environ.get("LD_LIBRARY_PATH", "")
    os.environ["LD_LIBRARY_PATH"] = (
        library_path + ":" + ld_lib_path if ld_lib_path else library_path
    )

    try:
        if runtime_data_yaml_filename is None:
            debuda_stub_args = [f"{port}"]
        else:
            debuda_stub_args = [f"{port}", "-y", f"{runtime_data_yaml_filename}"]
        if run_dirpath:
            debuda_stub_args += ["-r", run_dirpath]
        if wanted_devices:
            debuda_stub_args += ["-d"] + [str(d) for d in wanted_devices]

        
        debuda_stub = subprocess.Popen(
            [debuda_stub_path] + debuda_stub_args,
            preexec_fn=os.setsid,
            stdin=subprocess.PIPE, # We close by sending SIGTERM
            env=os.environ.copy(),
        )
    except:
        if os.path.islink(debuda_stub_path):
            if not os.path.exists(os.readlink(debuda_stub_path)):
                util.FATAL(f"Missing debuda-server-standalone. Try: make dbd")
        raise

    util.INFO("Debuda-server started.")
    return debuda_stub

# Terminates debuda-server spawned in connect_to_server
def stop_server(debuda_stub: subprocess.Popen):
    if debuda_stub is not None and debuda_stub.poll() is None:
        os.killpg(os.getpgid(debuda_stub.pid), signal.SIGTERM)
        time.sleep(0.1)
        if debuda_stub.poll() is None:
            util.VERBOSE("Debuda-server did not respond to SIGTERM. Sending SIGKILL...")
            os.killpg(os.getpgid(debuda_stub.pid), signal.SIGKILL)

        time.sleep(0.1)
        if debuda_stub.poll() is None:
            util.ERROR(
                f"Debuda-server did not respond to SIGKILL. The process {debuda_stub.pid} is still running. Please kill it manually."
            )
        else:
            util.INFO("Debuda-server terminated.")
