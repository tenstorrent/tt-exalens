# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump_regfile <core-loc> <regfile_id> [-d <D>...]

Arguments:
  core-loc     Either X-Y or R,C location of a core
  regfile_id   Register file to read from (0: SRCA, 1: SRCB, 2: DSTACC)

Options:
  -d <D>       Device ID. Optional and repeatable. Default: current device

Description:
  Prints specified regfile (SRCA/DSTACC) at core-loc location of the current chip.

  Note:
  Due to the architecture of SRCA, you can see only see last two faces written.
  SRCB is currently not supported.

Examples:
  dr 0,0 0
  dr 0,0 2 -d 0
"""

command_metadata = {
    "short": "dr",
    "type": "dev",
    "description": __doc__,
    "context": ["limited", "metal"],
}

from docopt import docopt

from ttlens.tt_uistate import UIState
from ttlens.tt_coordinate import OnChipCoordinate
from ttlens.tt_debug_tensix import TensixDebug
from ttlens.tt_unpack_regfile import unpack_data


def run(cmd_text, context, ui_state: UIState = None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])

    core_loc_str = args["<core-loc>"]
    regfile_id = int(args["<regfile_id>"])

    current_device_id = ui_state.current_device_id
    device_ids = args["-d"] if args["-d"] else [f"{current_device_id}"]
    device_array = []
    for device_id in device_ids:
        device_array.append(int(device_id, 0))

    for device_id in device_array:
        current_device = context.devices[device_id]
        core_loc = OnChipCoordinate.create(core_loc_str, device=current_device)

        debug_tensix = TensixDebug(core_loc, device_id, context)
        data = debug_tensix.read_regfile(regfile_id)
        df = debug_tensix.read_cfg_reg("ALU_FORMAT_SPEC_REG2_Dstacc")
        unpacked_data = unpack_data(data, df)

        for i in range(len(unpacked_data)):
            print(unpacked_data[i], end="\t")
            if i % 32 == 31:
                print()

    return None
