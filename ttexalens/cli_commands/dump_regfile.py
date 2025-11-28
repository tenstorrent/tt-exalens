# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump_regfile <core-loc> <regfile> [-d <D>...] [-t <num-tiles>]

Arguments:
  core-loc     Either X-Y or R,C location of a core
  regfile      Register file to read from (0: SRCA, 1: SRCB, 2: DSTACC)

Options:
  -d <D>                    Device ID. Optional and repeatable. Default: current device
  -t <num-tiles>            Number of tiles to read. Only effective for 32 bit formats on blackhole.

Description:
  Prints specified regfile (SRCA/DSTACC) at core-loc location of the current chip.

  Note:
  Due to the architecture of SRCA, you can see only see last two faces written.
  SRCB is currently not supported.
  Reading DSTACC on Wormhole as FP32 clobbers the register.

Examples:
  dr 0,0 0
  dr 0,0 SRCA
  dr 0,0 2 -d 1
  dr 0,0 dstacc -d 1
"""

command_metadata = {
    "short": "dr",
    "long": "dump-regfile",
    "type": "dev",
    "description": __doc__,
    "context": ["limited", "metal"],
}

from docopt import docopt

from ttexalens.uistate import UIState
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_tensix import TensixDebug
from ttexalens.util import INFO
from ttexalens.debug_tensix import TILE_SIZE


def print_regfile(data: list[int | float] | list[str]) -> None:
    for i in range(len(data)):
        if i % TILE_SIZE == 0:
            INFO(f"TILE ID: {i // TILE_SIZE}")
        print(data[i], end="\t")
        if i % 32 == 31:
            print()


def run(cmd_text, context, ui_state: UIState):
    args = docopt(__doc__, argv=cmd_text.split()[1:])

    core_loc_str = args["<core-loc>"]
    regfile = args["<regfile>"]
    num_tiles = int(args["-t"]) if args["-t"] else None

    current_device_id = ui_state.current_device_id
    device_ids = args["-d"] if args["-d"] else [f"{current_device_id}"]
    device_array = []
    for device_id in device_ids:
        device_array.append(int(device_id, 0))

    for device_id in device_array:
        current_device = context.devices[device_id]
        core_loc = OnChipCoordinate.create(core_loc_str, device=current_device)

        debug_tensix = TensixDebug(core_loc, device_id, context)
        data = debug_tensix.read_regfile(regfile, num_tiles)
        print_regfile(data)

    return None
