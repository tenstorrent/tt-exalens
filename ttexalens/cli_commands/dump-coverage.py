"""
Usage:
  dump-coverage <elf> [<gcno>] <outdir>

Description:
  Get coverage data for a given ELF.
  
  Given the currently running ELF (and optionally its gcno),
  extract coverage data from the device and place it into the
  specified output directory along with its gcno.

Examples:
  cov build/riscv-src/wormhole/callstack.trisc0.elf cov_dir
"""

command_metadata = {
    "short": "cov",
    "type": "high-level",
    "description": __doc__,
    "context": "limited",
    "common_option_names": ["--device", "--loc", "--verbose"]
}

from pathlib import Path
from ttexalens import util as util
from ttexalens import command_parser
from ttexalens.uistate import UIState
from ttexalens.coverage import dump_coverage

def run(cmd_text, context, ui_state: UIState):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
        common_option_names=command_metadata["common_option_names"]
    )

    elf_path = Path(dopt.args["<elf>"]).resolve()
    outdir = Path(dopt.args["<outdir>"]).resolve()
    gcno_arg = dopt.args.get("<gcno>")
    gcno_path = Path(gcno_arg).resolve() if gcno_arg else None
    
    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            try:
                dump_coverage(context, loc, elf_path, outdir, gcno_path)
                util.VERBOSE(f"Coverage data dumped for device {device.id} loc {loc}")
            except Exception as e:
                util.ERROR(f"dump-coverage: {e}")
