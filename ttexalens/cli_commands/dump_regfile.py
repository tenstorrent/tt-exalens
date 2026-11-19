# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump_regfile <regfile> [ -l <loc> ] [ -t <num-tiles> ] [ -d <device> ] [ --neo <neo-id> ]

Arguments:
  regfile      Register file to read from (0: SRCA, 1: SRCB, 2: DSTACC)

Options:
  -t <num-tiles>            Number of tiles to read. Only effective for 32 bit formats on blackhole and for DSTACC on quasar.

Description:
  Prints the specified regfile (SRCA/DSTACC).

  Note:
  Due to the architecture of SRCA, you can see only see last two faces written.
  SRCB is currently not supported.
  Reading DSTACC on Wormhole as FP32 clobbers the register.
  Currently on Quasar only DSTACC is supported.
Examples:
  dr 0
  dr SRCA -l 0,0
  dr 0 -l 0,0 -d 1
  dr 2 -l 0,0
  dr dstacc -l 0,0 -d 1
"""

from collections.abc import Sequence

from ttexalens.context import Context
from ttexalens.device import Device
from ttexalens.uistate import UIState
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.util import ERROR, INFO
from ttexalens.debug_tensix import TILE_SIZE
from ttexalens.command_parser import CommandMetadata, CommonCommandOptions, tt_docopt

command_metadata = CommandMetadata(
    short_name="dr",
    long_name="dump-regfile",
    type="dev",
    description=__doc__,
    common_option_names=[
        CommonCommandOptions.Device,
        CommonCommandOptions.Location,
        CommonCommandOptions.Neo,
    ],
)


def print_regfile(data: Sequence[int | float | str]) -> None:
    for i in range(len(data)):
        if i % TILE_SIZE == 0:
            INFO(f"TILE ID: {i // TILE_SIZE}")
        print(data[i], end="\t")
        if i % 32 == 31:
            print()


def run(cmd_text: str, context: Context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    args = dopt.args

    regfile: str = args["<regfile>"]
    num_tiles: int | None = int(args["-t"]) if args["-t"] else None

    device: Device
    location: OnChipCoordinate
    for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state):
        INFO(f"Dump regfile on device {device.id}")
        for location in dopt.for_each(CommonCommandOptions.Location, context, ui_state, device=device):
            neo_id = dopt.get_neo_id(ui_state, location.noc_block)
            INFO(f"Location {location.to_user_str(neo_id)}")
            tensix_debug = location.noc_block.get_tensix_debug(neo_id)
            if tensix_debug is None:
                ERROR("This location does not have a Tensix.")
                continue
            data = tensix_debug.read_regfile(regfile, num_tiles)
            print_regfile(data)

    return None
