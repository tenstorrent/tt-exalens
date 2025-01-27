# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from ttlens import tt_commands
from ttlens.tt_debug_tensix import TensixDebug
from docopt import docopt

command_metadata = {
    "short": "cfg",
    "type": "high-level",
    "description": __doc__,
    "context": ["limited"],
    "common_option_names": [],
}


def run(cmd_text, context, ui_state=None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])
