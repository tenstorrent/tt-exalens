# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  callstack <elf-file> [-r <risc>] [-m <max-depth>] [-v] [-d <device>] [-l <loc>]

Description:
  Prints callstack using provided elf for a given RiscV core.

Options:
  -r <risc>           RiscV name (brisc, triscs0, trisc1, trisc2, erisc, all). [default: all]
  -m <max-depth>      Maximum depth of callstack. [Default: 100]

Examples:
  callstack build/riscv-src/wormhole/sample.brisc.elf -r 0
"""

command_metadata = {
    "short": "bt",
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "common_option_names": ["--device", "--loc", "--verbose"],
}

import os
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.uistate import UIState

from ttexalens import command_parser
from ttexalens import util
from ttexalens.device import Device


def run(cmd_text, context, ui_state: UIState = None):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
        common_option_names=command_metadata["common_option_names"],
    )

    verbose = dopt.args["-v"]
    limit = int(dopt.args["-m"])
    elf_path = dopt.args["<elf-file>"]
    stop_on_main = True

    if not os.path.exists(elf_path):
        util.ERROR(f"File {elf_path} does not exist")
        return

    device: Device
    for device in dopt.for_each("--device", context, ui_state):
        loc: OnChipCoordinate
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            for risc_name in dopt.for_each("--risc", context, ui_state):
                risc_debug = device.get_risc_debug(loc, risc_name, verbose=verbose)
                if risc_debug.is_in_reset():
                    util.WARN(f"RiscV core {risc_name} on location {loc.to_user_str()} is in reset")
                    continue
                callstack = risc_debug.get_callstack(elf_path, limit, stop_on_main)
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
