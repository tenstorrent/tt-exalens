# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-coverage <elf> <gcda_path> [<gcno_copy_path>] [-d <device>...] [-l <loc>]

Arguments:
  device          ID of the device [default: current active]
  loc             Location identifier (e.g. 0-0) [default: current active]
  elf             Path to the currently running ELF
  gcda_path       Output path for the gcda
  gcno_copy_path  Optional path to copy the gcno file

Description:
  Get coverage data for a given ELF. Extract the gcda from the given core
  and place it into the output directory along with its gcno.

Examples:
  cov build/riscv-src/wormhole/callstack.coverage.trisc0.elf coverage/callstack.gcda
  cov build/riscv-src/wormhole/cov_test.coverage.brisc.elf coverage/cov_test.gcda coverage/cov_test.gcno
"""

command_metadata = {
    "short": "cov",
    "type": "high-level",
    "description": __doc__,
    "context": "limited",
    "common_option_names": ["--device", "--loc", "--verbose"],
}

from ttexalens import util
from ttexalens import command_parser
from ttexalens.tt_exalens_lib import check_context, parse_elf
from ttexalens.uistate import UIState
from ttexalens.coverage import dump_coverage


def run(cmd_text, context, ui_state: UIState) -> list:
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
        common_option_names=command_metadata["common_option_names"],
    )

    elf_path = dopt.args["<elf>"]
    gcda_path = dopt.args["<gcda_path>"]
    gcno_arg = dopt.args.get("<gcno_copy_path>")
    gcno_path = gcno_arg if gcno_arg else None
    context = check_context(context)
    elf = parse_elf(elf_path, context)

    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            try:
                dump_coverage(elf, loc, gcda_path, gcno_path)
                util.VERBOSE(f"Coverage data dumped for device {device.id} loc {loc}:")
                if gcno_path:
                    util.VERBOSE(gcno_path)
                util.VERBOSE(gcda_path)
            except Exception as e:
                util.ERROR(f"dump-coverage: {e}")

    return []
