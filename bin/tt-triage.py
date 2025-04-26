#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
TT Triage:
  Analyze the device state to determine the cause of failure.

Usage:
  tt-triage.py [-v | --verbose] [--dev=<device_id>]...

Options:
  -h --help         Show this screen.
  --dev=<device_id> Specify the device id  [default: all]
  -v --verbose      Print verbose output.  [default: False]
"""

# Build the executable with:
#   pyinstaller tt-triage.spec

RST = "\033[0m"
BLUE = "\033[34m"   # For good values
RED = "\033[31m"    # For bad values
GREEN = "\033[32m"  # For instructions
ORANGE = "\033[33m" # For warnings
VERBOSE_CLR = "\033[94m"   # For verbose output

try:
    from docopt import docopt
    import yaml
except ImportError as e:
    missing_module = str(e).split("'")[1]
    print(f"Module '{missing_module}' not found. Please install required modules using: {GREEN}pip install docopt, pyyaml{RST}")
    exit(1)

try:
    from ttexalens.tt_exalens_init import init_ttexalens
    from ttexalens.tt_exalens_lib import read_from_device, read_words_from_device, arc_msg
    from ttexalens.coordinate import OnChipCoordinate
except ImportError as e:
    print(f"Module '{e}' not found. Please install tt-exalens: {GREEN}", end="")
    print("""
  sudo apt update && sudo apt install -y software-properties-common build-essential libyaml-cpp-dev libhwloc-dev libzmq3-dev libgtest-dev libgmock-dev xxd ninja-build ccache
  python3 -m pip install --upgrade pip
  git submodule update --init --recursive
  pip install -r ttexalens/requirements.txt
  make build
  python3 -m pip install -e .
  export PATH=$PATH:/home/$USER/.local/bin
    """)
    exit(1)

def verbose(msg):
    """Print message if verbose mode is enabled (-v)."""
    if VERBOSE:
        print(f"{VERBOSE_CLR}- {msg}{RST}")

def title(msg):
    """Print a title."""
    verbose(f"{GREEN}=== {msg} ==={RST}")

def check_L1(device_id):
    """Checking location 0x0 of each core's L1 for the presence of FW."""
    title(check_L1.__doc__)

    device = context.devices[device_id]
    addr = 0x0
    for loc in device.get_block_locations(block_type="functional_workers"):
        data = read_words_from_device(loc, addr, device_id=device_id, word_count=1, context=context)
        if data[0] != 0x3800306f:
            print(f"NOC at {loc} addr 0x{addr:08x}: {RED}0x{data[0]:08x}{RST}. Expected {BLUE}0x3800306f{RST}")
            raise Exception(check_L1.__doc__)

def main(args):
    global context
    context = init_ttexalens(use_noc1=False)
    device_ids = list(context.devices.keys())

    # Pupulate integer array with device ids
    if len(args['--dev']) == 1 and args['--dev'][0].lower() == 'all':
        device_ids = [ int(id) for id in context.devices.keys() ]
    else:
        device_ids = [ int(id) for id in args['--dev'] ]

    verbose(f"Device IDs: {device_ids}")

    for device_id in device_ids:
        check_L1(device_id)

    print (f"{GREEN}DONE: OK{RST}")

if __name__ == "__main__":
    args = docopt(__doc__)
    VERBOSE = args['--verbose']
    main(args)