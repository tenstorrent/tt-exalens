# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  interfaces

Description:
  Shows unique wafer information for devices connected via each interface. Used
  to establish a mapping between the same device on different interfaces.

Examples:
  interfaces             # Shows op mapping for all devices
"""  # Note: Limit the above comment to 100 characters in width

command_metadata = {
    "short": "if",
    "long": "interfaces",
    "type": "dev",
    "description": __doc__,
    "context": ["limited", "metal"],
}

from docopt import docopt
from ttexalens.context import Context

TEST_ID_SIZE = 48


def decode_test_id(test_id_data):
    data = test_id_data.decode("UTF-8")
    wafer_info = {
        "lot_id": (data[0:10]).replace("\x00", ""),
        "wafer_id": (data[10:23]).replace("\x00", ""),
        "wafer_alias": (data[24:26]).replace("\x00", ""),
        "x_coord": (data[26:29]).replace("\x00", ""),
        "y_coord": (data[29:32]).replace("\x00", ""),
        "binning": (data[33:40]).replace("\x00", ""),
        "test_program_rev": data[41:47].replace("\x00", ""),
    }
    return wafer_info


# There are 3 ways to read the test id from the device
# raw pci read, jtag axi read, and arc noc read


def read_axi_size(context: Context, device_id, address, size):
    data = b""
    noc_id = 0
    arc_location: tuple[int, int] = context.devices[device_id]._block_locations["arc"][0].to("noc0")

    for i in range(0, size, 4):
        data += context.server_ifc.read32(noc_id, device_id, arc_location[0], arc_location[1], address + i).to_bytes(4, byteorder="little")
    return data[:size]


def read_pci_raw_size(context: Context, device_id, address, size):
    data = b""
    for i in range(0, size, 4):
        data += context.server_ifc.pci_read32_raw(device_id, address + i).to_bytes(4, byteorder="little")
    return data[:size]


def read_noc_size(context: Context, device_id, nocx, nocy, address, size):
    noc_id = 1 if context.use_noc1 else 0
    return context.server_ifc.read(noc_id, device_id, nocx, nocy, address, size)


def run(cmd_text, context: Context, ui_state=None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])
    device = context.devices[0]

    try:
        efuse_pci = device.EFUSE_PCI
        efuse_noc = device.EFUSE_NOC
        efuse_jtag_axi = device.EFUSE_JTAG_AXI
    except:
        raise Exception(f"Unsupported arch {device._arch}")

    devices_list = list(context.devices.keys())
    for device_id in devices_list:
        arc_location: tuple[int, int] = context.devices[device_id]._block_locations["arc"][0].to("noc0")
        print(
            f"NOC Device {device_id}: "
            + str(
                decode_test_id(
                    read_noc_size(
                        context,
                        device_id,
                        *arc_location,
                        efuse_noc,
                        TEST_ID_SIZE,
                    )
                )
            )
        )

    for device_id in devices_list:
        # mmio chips
        if context.devices[device_id]._has_mmio:
            if context.devices[device_id]._has_jtag:
                print(
                    f"JTAG Device {device_id}: "
                    + str(decode_test_id(read_axi_size(context, device_id, efuse_jtag_axi, TEST_ID_SIZE)))
                )
            else: 
                print(
                    f"PCI Device {device_id}: "
                    + str(decode_test_id(read_pci_raw_size(context, device_id, efuse_pci, TEST_ID_SIZE)))
                )

    navigation_suggestions: list[int] = []
    return navigation_suggestions
