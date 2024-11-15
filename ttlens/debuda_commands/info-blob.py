# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  info-blob [ -c <core-loc>... ] [-d <device-id>...]

Options:
  -d <device-id>  Device ID. Optional and repeatable. Default: current device
  -c <core-loc>   Either X-Y or R,C location of the core. Optional and repeatable. Default: current core

Description:
  Reads and prints information on blob.

Examples:
    info-blob -c 18-18 -c 19-19 -d 0  # Print all epoch_ids of cores 18-18 and 19-19 on device 0
"""

command_metadata = {
    "short": "ib", 
    "type": "dev", 
    "description": __doc__, 
    "context": ["buda"],
}

from docopt import docopt

from ttlens.tt_uistate import UIState

from ttlens import tt_util as util
from ttlens.tt_firmware import ELF
from ttlens.tt_coordinate import OnChipCoordinate
from ttlens.tt_debuda_lib import read_words_from_device


def pretty_print_overlay_blob_register_settings(context, device_id, core_loc, blob_address):
    """
    Given a blob address, print the register settings in a nice way.
    """
    blob = read_words_from_device(core_loc, blob_address, device_id, 1, context)[0]
    print(
        f"  Blob read from address 0x{blob_address:08x}: 0x{blob:08x}: ... <to be implemented> ..."
    )


def print_info_blob(context, device_id, core_loc):
    """
    Get the blob address from the epoch info struct and print the register settings in a nice way.
    """
    mem_reader = ELF.get_mem_reader(context, device_id=device_id, core_loc=core_loc)
    num_input_streams = context.elf.read_path("brisc.EPOCH_INFO_PTR.num_inputs", mem_reader)[0]
    print(f"Number of input streams: {num_input_streams}")
    for s in range(num_input_streams):
        blob_address = context.elf.read_path(
            f"brisc.EPOCH_INFO_PTR.inputs[{s}]->blob_start_addr", mem_reader
        )
        # print (f"  Input stream {s} blob address: 0x{blob_address[0]:08x}")
        pretty_print_overlay_blob_register_settings(
            context, device_id, core_loc, blob_address[0]
        )  ## another user written plugin to dump these in a nice way


def run(cmd_text, context, ui_state: UIState = None):
    args = docopt(command_metadata["description"], argv=cmd_text.split()[1:])

    current_device_id = ui_state.current_device_id
    current_device = context.devices[current_device_id]
    current_loc = ui_state.current_location

    core_locs = args["-c"] if args["-c"] else [current_loc.to_str()]
    core_array = []
    for core_loc in core_locs:
        coord = OnChipCoordinate.create(core_loc, current_device)
        core_array.append(coord)

    device_ids = args["-d"] if args["-d"] else [f"{current_device_id}"]
    device_array = []
    for device_id in device_ids:
        did = int(device_id, 0)
        device_array.append(context.devices[did])

    for device in device_array:
        for core_loc in core_array:
            util.PRINT(f"Reading from device {device.id()}, core {core_loc.to_str()}")
            print_info_blob(context, device.id(), core_loc)
