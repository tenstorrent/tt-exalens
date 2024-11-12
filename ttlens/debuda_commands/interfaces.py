# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  interfaces

Description:
  Shows a device summary. When no argument is supplied, it iterates through all devices used by the
  currently loaded netlist.

Examples:
  interfaces             # Shows op mapping for all devices
"""  # Note: Limit the above comment to 100 characters in width

command_metadata = {
    "short": "if",
    "long": "interfaces",
    "type": "high-level",
    "description": __doc__,
    "context": ["limited", "buda", "metal"],
}

from docopt import docopt

from ttlens import tt_util as util
from ttlens  import tt_device
from ttlens.tt_debuda_context import LimitedContext
from ttlens.tt_debuda_lib import read_words_from_device, read_from_device
from ttlens.tt_coordinate import OnChipCoordinate

TEST_ID_SIZE = 48
def decode_test_id(test_id_data):
    data = test_id_data.decode("UTF-8")
    wafer_info = {
        "lot_id": (data[0:7] + data[8:10]).replace("\x00", ""),
        "wafer_id": (data[10:15] + data[16:23]).replace("\x00", ""),
        "wafer_alias": (data[24:26]).replace("\x00", ""),
        "x_coord": (data[26:29]).replace("\x00", ""),
        "y_coord": (data[29:31] + data[32]).replace("\x00", ""),
        "binning": (data[33:39] + data[40]).replace("\x00", ""),
        "test_program_rev": data[41:47].replace("\x00", "")
    }
    return wafer_info

# There are 3 ways to read the test id from the device
# raw pci read, jtag axi read, and arc noc read
EFUSE_PCI = 0x1FF42200
EFUSE_JTAG_AXI = 0x80042200
EFUSE_NOC = 0x880042200

def read_axi_size(device_id, address, size):
    data = b""
    for i in range(0, size, 4):
        data += tt_device.SERVER_IFC.jtag_read32_axi(
            device_id, address + i
        ).to_bytes(4, byteorder="little")
    return data[:size]

def read_pci_raw_size(device_id, address, size):
    data = b""
    for i in range(0, size, 4):
        data += tt_device.SERVER_IFC.pci_read32_raw(
            device_id, address + i
        ).to_bytes(4, byteorder="little")
    return data[:size]

def read_noc_size(device_id, nocx, nocy, address, size):
    return tt_device.SERVER_IFC.pci_read( device_id, nocx, nocy, address, size)


def run(cmd_text, context, ui_state=None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])

    devices_list = list(context.devices.keys())
    for device_id in devices_list:
      # all chips
      print(f"NOC Device {device_id}: " + str(decode_test_id(read_noc_size(device_id, 0, 10, EFUSE_NOC, TEST_ID_SIZE))))

    for device_id in devices_list:
      # mmio chips
      try:
        print(f"PCI Device {device_id}: " + str(decode_test_id(read_pci_raw_size(device_id, EFUSE_PCI, TEST_ID_SIZE))))
      except Exception as e:
        pass

    for device_id in devices_list:
      # jtag chips
      try:
        print(f"JTAG Device {device_id}: " + str(decode_test_id(read_axi_size(device_id, EFUSE_JTAG_AXI, TEST_ID_SIZE))))
      except Exception as e:
        pass

    navigation_suggestions = []
    return navigation_suggestions
