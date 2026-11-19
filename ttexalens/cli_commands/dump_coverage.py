# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-coverage <elf> <gcda_path> [<gcno_copy_path>] [-d <device>...] [-l <loc>]

Arguments:
  elf             Path to the currently running ELF
  gcda_path       Output path for the gcda
  gcno_copy_path  Optional path to copy the gcno file

Description:
  Get coverage data for a given ELF. Extract the gcda from the given core
  and place it into the output directory along with its gcno.

Examples:
  re build/riscv-src/wormhole/cov_test.coverage.brisc.elf -r brisc # Pre-requisite: we have to run the elf before running coverage
  cov build/riscv-src/wormhole/cov_test.coverage.brisc.elf cov_test.gcda cov_test.gcno
"""

import os

from ttexalens import util
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
from ttexalens.tt_exalens_lib import check_context, parse_elf
from ttexalens.uistate import UIState
from ttexalens.coverage import dump_coverage
from ttexalens.command_parser import CommandMetadata, tt_docopt, CommonCommandOptions

command_metadata = CommandMetadata(
    short_name="cov",
    long_name="dump-coverage",
    type="high-level",
    description=__doc__,
    common_option_names=[CommonCommandOptions.Device, CommonCommandOptions.Location],
)


def _path_in_core_directory(path: str, device: Device, loc: OnChipCoordinate) -> str:
    directory = os.path.join(os.path.dirname(path), f"device{device.id}_{loc.to_str('noc0')}")
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, os.path.basename(path))


def run(cmd_text: str, context: Context, ui_state: UIState) -> list[dict[str, str]]:
    dopt = tt_docopt(command_metadata, cmd_text)
    elf_path = dopt.args["<elf>"]
    gcda_path = dopt.args["<gcda_path>"]
    gcno_arg = dopt.args.get("<gcno_copy_path>")
    gcno_path = gcno_arg if gcno_arg else None
    context = check_context(context)
    elf = parse_elf(elf_path, context)

    device: Device
    loc: OnChipCoordinate
    targets = [
        (device, loc)
        for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state)
        for loc in dopt.for_each(CommonCommandOptions.Location, context, ui_state, device=device)
    ]
    for device, loc in targets:
        target_gcda_path, target_gcno_path = gcda_path, gcno_path
        if len(targets) > 1:
            # Each core gets its own subdirectory, so cores do not overwrite each other's files
            # and the gcda and gcno keep their names
            target_gcda_path = _path_in_core_directory(gcda_path, device, loc)
            if gcno_path:
                target_gcno_path = _path_in_core_directory(gcno_path, device, loc)
        try:
            dump_coverage(elf, loc, target_gcda_path, target_gcno_path)
            if util.VERBOSE_ENABLED:
                util.VERBOSE(f"Coverage data dumped for device {device.id} loc {loc}:")
            if target_gcno_path:
                if util.VERBOSE_ENABLED:
                    util.VERBOSE(target_gcno_path)
            if util.VERBOSE_ENABLED:
                util.VERBOSE(target_gcda_path)
        except Exception as e:
            util.ERROR(f"dump-coverage: {e}")

    return []
