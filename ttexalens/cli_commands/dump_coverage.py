# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-coverage <elf> <gcda_path> [<gcno_copy_path>] [-d <device>] [-l <loc>]

Arguments:
  elf             Path to the currently running ELF
  gcda_path       Output path for the gcda. With several cores, each core's file gets the device id and the noc0 location (dev0_1-1) before the extension
  gcno_copy_path  Optional path to copy the gcno file, named per core the same way

Description:
  Get coverage data for a given ELF. Extract the gcda from the given core
  and place it into the output directory along with its gcno.
  Cores that cannot be dumped are reported and skipped.

Examples:
  re build/riscv-src/wormhole/cov_test.coverage.brisc.elf -r brisc # Pre-requisite: we have to run the elf before running coverage
  cov build/riscv-src/wormhole/cov_test.coverage.brisc.elf cov_test.gcda cov_test.gcno
"""

from ttexalens import util
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.tt_exalens_lib import check_context, parse_elf
from ttexalens.uistate import UIState
from ttexalens.coverage import dump_coverage, per_core_path
from ttexalens.command_parser import CommandMetadata, tt_docopt, CommonCommandOptions

command_metadata = CommandMetadata(
    short_name="cov",
    long_name="dump-coverage",
    type="high-level",
    description=__doc__,
    common_option_names=[CommonCommandOptions.Device, CommonCommandOptions.Location],
)


def run(cmd_text: str, context: Context, ui_state: UIState) -> list[dict[str, str]]:
    dopt = tt_docopt(command_metadata, cmd_text)
    elf_path = dopt.args["<elf>"]
    gcda_path = dopt.args["<gcda_path>"]
    gcno_arg = dopt.args.get("<gcno_copy_path>")
    gcno_path = gcno_arg if gcno_arg else None
    context = check_context(context)
    elf = parse_elf(elf_path, context)

    targets: list[OnChipCoordinate] = []
    for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state):
        for loc in dopt.for_each(CommonCommandOptions.Location, context, ui_state, device=device):
            targets.append(loc)
    targets = list(dict.fromkeys(targets))
    several = len(targets) > 1
    dumped = 0

    for loc in targets:
        gcda = per_core_path(gcda_path, loc) if several else gcda_path
        gcno = per_core_path(gcno_path, loc) if several and gcno_path else gcno_path
        try:
            dump_coverage(elf, loc, gcda, gcno)
            dumped += 1
            util.INFO(
                f"dump-coverage: device {loc.device.id} loc {loc.to_user_str()}: {gcda}" + (f", {gcno}" if gcno else "")
            )
        except Exception as e:
            message = f"dump-coverage: device {loc.device.id} loc {loc.to_user_str()} skipped: {e}"
            if several:
                util.WARN(message)
            else:
                util.ERROR(message)

    if several:
        util.INFO(f"dump-coverage: dumped {dumped} of {len(targets)} cores")

    return []
