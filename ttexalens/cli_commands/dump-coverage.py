# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-coverage <core-loc> <elf> <outdir> [<gcno>] [-d <D>...]

Arguments:
  core-loc      Core location (e.g., 0,0)
  elf           Path to the ELF file that is currently running
  outdir        Output directory to place the gcno and gcda
  gcno          Optional path to the gcno file

Options:
  -d <D>        Device ID. Optional and repeatable. Default: current device

Description:
  Get coverage data for a given ELF. Extract coverage from the specified core
  or DRAM channel and place it into the output directory along with its gcno.

Examples:
  cov 0,0 build/riscv-src/wormhole/sample.trisc0.elf cov_dir
"""

command_metadata = {
    "short": "cov",
    "type": "high-level",
    "description": __doc__,
    "context": "limited",
    "common_option_names": ["--verbose"],
}

from pathlib import Path
from ttexalens import util
from ttexalens import command_parser
from ttexalens.uistate import UIState
from ttexalens.coverage import dump_coverage


def run(cmd_text, context, ui_state: UIState):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
        common_option_names=command_metadata["common_option_names"],
    )

    core_loc = dopt.args["<core-loc>"]
    elf_path = Path(dopt.args["<elf>"]).resolve()
    outdir = Path(dopt.args["<outdir>"]).resolve()
    gcno_arg = dopt.args.get("<gcno>")
    gcno_path = Path(gcno_arg).resolve() if gcno_arg else None

    device_ids = dopt.args.get("-d") or [str(ui_state.current_device_id)]

    for id in device_ids:
        device = context.devices[int(id, 0)]
        try:
            dump_coverage(context, core_loc, elf_path, outdir, gcno_path)
            util.VERBOSE(f"Coverage data dumped for device {device.id} loc {core_loc}")
        except Exception as e:
            util.ERROR(f"dump-coverage: {e}")
