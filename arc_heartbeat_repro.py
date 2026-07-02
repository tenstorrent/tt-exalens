# SPDX-FileCopyrightText: (c) 2026 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
"""
Pure-UMD ARC heartbeat repro.

Goal: isolate whether the "telemetry reads 0 when noc_id != init NOC" behavior is a
TT-ExaLens bug or a UMD bug. This script uses ONLY tt_umd (UMD) APIs -- no exalens
device.py / tt_exalens_lib wrappers -- so anything it reproduces is UMD-level.

What exalens does under the hood (for reference):
  - init_ttexalens(use_noc1=...) sets the thread-local NOC, then runs
    tt_umd.TopologyDiscovery.discover() under that NOC.
  - read_arc_telemetry_entry(noc_id=...) calls tt_umd.set_thread_noc_id(noc_id) and
    then reads through the cached tt_umd ArcTelemetryReader.

So here we do exactly that, by hand, and toggle the thread NOC for each read.

Usage:
    python arc_heartbeat_repro.py            # discover under NOC0 (mirrors use_noc1=False)
    python arc_heartbeat_repro.py --noc1     # discover under NOC1 (mirrors use_noc1=True)
"""

import sys
import time
import tt_umd

NOC0 = tt_umd.NocId.NOC0
NOC1 = tt_umd.NocId.NOC1

init_noc1 = "--noc1" in sys.argv
init_noc = NOC1 if init_noc1 else NOC0

# --- Discover the topology under the chosen init NOC (mirrors init_ttexalens) ---
tt_umd.set_thread_noc_id(init_noc)

options = tt_umd.TopologyDiscoveryOptions()
options.cmfw_mismatch_action = tt_umd.TopologyDiscoveryOptions.Action.IGNORE
options.cmfw_unsupported_action = tt_umd.TopologyDiscoveryOptions.Action.IGNORE
options.eth_fw_mismatch_action = tt_umd.TopologyDiscoveryOptions.Action.IGNORE
options.unexpected_routing_firmware_config = tt_umd.TopologyDiscoveryOptions.Action.IGNORE
options.eth_fw_heartbeat_failure = tt_umd.TopologyDiscoveryOptions.Action.IGNORE
options.wait_on_ethernet_link_training = True
options.use_safe_api = True

cluster_descriptor, devices = tt_umd.TopologyDiscovery.discover(options, tt_umd.IODeviceType.PCIe)
chip_id = sorted(cluster_descriptor.get_all_chips())[0]
device = devices[chip_id]

reader = device.get_arc_telemetry_reader()
tag = tt_umd.TelemetryTag.AICLK

print(f"Discovered under {'NOC1' if init_noc1 else 'NOC0'}; reading TIMER_HEARTBEAT over both NOCs.\n")


def read_over(noc, noc_name):
    tt_umd.set_thread_noc_id(noc)
    available = reader.is_entry_available(tag)
    value = reader.read_entry(tag) if available else None
    print(f"  {noc_name}: available={available} value={value}")


for i in range(5):
    print(f"iter {i}:")
    read_over(NOC0, "NOC0")
    read_over(NOC1, "NOC1")
    time.sleep(0.1)
