# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  callstack <elf-files> [-o <offsets>] [-r <risc>] [-m <max-depth>] [-d <device>] [-l <loc>]

Description:
  Prints callstack using provided elf for a given RiscV core.

Arguments:
    <elf-files>       Paths to the elf files to be used for callstack, comma separated.

Options:
  -o <offsets>        List of offsets for each elf file, comma separated.
  -m <max-depth>      Maximum depth of callstack. [Default: 100]

Examples:
  callstack build/riscv-src/wormhole/sample.brisc.elf -r brisc
"""

import os
from ttexalens.device import Device
from ttexalens.uistate import UIState

from ttexalens import util
import ttexalens.tt_exalens_lib as lib
from ttexalens.command_parser import CommandMetadata, tt_docopt, CommonCommandOptions

command_metadata = CommandMetadata(
    short_name="bt",
    type="low-level",
    description=__doc__,
    common_option_names=[CommonCommandOptions.Device, CommonCommandOptions.Location, CommonCommandOptions.Risc],
)


def run(cmd_text, context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)

    limit = int(dopt.args["-m"])
    elf_paths = dopt.args["<elf-files>"].split(",")
    offsets: list[int | None] = (
        [int(offset, 0) for offset in dopt.args["-o"].split(",")]
        if dopt.args["-o"]
        else [None for _ in range(len(elf_paths))]
    )
    if len(offsets) != len(elf_paths):
        util.ERROR("Number of offsets must match the number of elf files")
        return
    stop_on_main = True

    for elf_path in elf_paths:
        if not os.path.exists(elf_path):
            util.ERROR(f"File {elf_path} does not exist")
            return

    elfs = [lib.parse_elf(elf_path, context) for elf_path in elf_paths]

    device: Device
    for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state):
        for loc in dopt.for_each(CommonCommandOptions.Location, context, ui_state, device=device):
            for risc_name in dopt.for_each(CommonCommandOptions.Risc, context, ui_state, device=device, location=loc):
                if risc_name == "first risc":
                    noc_block = device.get_block(loc)
                    riscs = noc_block.all_riscs
                    if len(riscs) > 0:
                        risc_name = riscs[0].risc_location.risc_name
                    else:
                        util.ERROR(f"No RISC-V cores found at location {loc}")
                        return
                callstack = lib.callstack(
                    location=loc,
                    elfs=elfs,
                    offsets=offsets,
                    risc_name=risc_name,
                    max_depth=limit,
                    stop_on_main=stop_on_main,
                )
                print(
                    f"Location: {util.CLR_INFO}{loc.to_user_str()}{util.CLR_END}, core: {util.CLR_WHITE}{risc_name}{util.CLR_END}"
                )

                frame_number_width = len(str(len(callstack) - 1))
                for i, frame in enumerate(callstack):
                    print(f"  #{i:<{frame_number_width}} ", end="")
                    if frame.pc is not None:
                        print(f"{util.CLR_BLUE}0x{frame.pc:08X}{util.CLR_END} in ", end="")
                    if frame.function_name is not None:
                        print(f"{util.CLR_YELLOW}{frame.function_name}{util.CLR_END} () ", end="")
                    if frame.file is not None:
                        print(f"at {util.CLR_GREEN}{frame.file} {frame.line}:{frame.column}{util.CLR_END}", end="")
                    print()

    return None
