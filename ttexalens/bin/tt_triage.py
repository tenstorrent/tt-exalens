#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
TT Triage:
  Analyze the device state to determine the cause of failure.

Usage:
  tt-triage [--halt-on-error] [-v | --verbose] [-V | --vverbose] [--dev=<device_id>]...

Options:
  -h --help         Show this screen.
  --dev=<device_id> Specify the device id       [default: all]
  -v --verbose      Print verbose output.       [default: False]
  -V --vverbose     Print more verbose output.  [default: False]
  --halt-on-error   Halt on error.              [default: False]
"""

# Setup library paths first
import os
import sys

# When packaged with PyInstaller, _MEIPASS is defined and contains the path to the bundled libraries
bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
os.environ['LD_LIBRARY_PATH'] = bundle_dir + os.pathsep + os.environ.get('LD_LIBRARY_PATH', '')

import time
from tabulate import tabulate

# Build the executable with:
#   pyinstaller tt-triage.spec

RST = "\033[0m"
BLUE = "\033[34m"   # For good values
RED = "\033[31m"    # For bad values
GREEN = "\033[32m"  # For instructions
ORANGE = "\033[33m" # For warnings
VERBOSE_CLR = "\033[94m"   # For verbose output

# Global variables for verbosity settings
VERBOSE = False
VVERBOSE = False
context = None

try:
    from docopt import docopt
    import yaml
except ImportError as e:
    missing_module = str(e).split("'")[1]
    print(f"Module '{missing_module}' not found. Please install required modules using: {GREEN}pip install docopt, pyyaml{RST}")
    exit(1)

try:
    from ttexalens.tt_exalens_init import init_ttexalens
    from ttexalens.tt_exalens_lib import read_from_device, read_words_from_device, read_word_from_device, write_words_to_device,arc_msg
    from ttexalens.coordinate import OnChipCoordinate
    from ttexalens.reg_access_yaml import YamlRegisterMap
    from ttexalens.reg_access_json import JsonRegisterMap
    from ttexalens.reg_access_common import set_verbose, DEFAULT_TABLE_FORMAT
    from ttexalens.device import Device
    from ttexalens.hw.tensix.wormhole.wormhole import WormholeDevice
    from ttexalens.hw.tensix.blackhole.blackhole import BlackholeDevice
except ImportError as e:
    print(f"Module '{e}' not found. Please install tt-exalens: {GREEN}", end="")
    print("""
  sudo apt update && sudo apt install -y software-properties-common build-essential libyaml-cpp-dev libhwloc-dev libzmq3-dev libgtest-dev libgmock-dev xxd ninja-build ccache
  python3 -m pip install --upgrade pip
  git submodule update --init --recursive
  pip install -r ttexalens/requirements.txt
  make build
  python3 -m pip install .
  export PATH=$PATH:/home/$USER/.local/bin
    """)
    exit(1)

class TTTriageError(Exception):
    """Base class for TT Triage errors."""
    pass

def raiseTTTriageError(msg):
    """Raise a TT Triage error."""
    if HALT_ON_ERROR:
        raise TTTriageError(msg)
    else:
        print(f"{RED}ERROR: {msg}{RST}")

def verbose(msg):
    """Print message if verbose mode is enabled (-v)"""
    if VERBOSE or VVERBOSE:
        print(f"{VERBOSE_CLR}{msg}{RST}")

def vverbose(msg):
    """Print message if verbose mode is enabled (-vv)."""
    if VVERBOSE:
        print(f"{VERBOSE_CLR}{msg}{RST}")

def title(msg):
    """Print a title."""
    print(f"{GREEN}= {msg}{RST}")

def check_ARC(dev):
    """Checking that ARC heartbeat is running. Estimating ARC uptime (-v)."""
    title(check_ARC.__doc__)

    arc_core_loc = dev.get_arc_block_location()
    def arc_read(addr: int) -> int:
        """Read ARC register using PCI->NOC->ARC."""
        value = read_word_from_device(arc_core_loc, addr)
        return value

    # Postcode must be correct (C0DE)
    # postcode = dev.ARC.ARC_RESET.SCRATCH[0].read()
    postcode = arc_read(0x880030060)
    if postcode & 0xFFFF0000 != 0xC0DE0000:
        print(f"ARC postcode: {RED}0x{postcode:08x}{RST}. Expected {BLUE}0xc0de____{RST}")
        raiseTTTriageError(check_ARC.__doc__)

    # Heartbeat must be increasing
    # heartbeat_0 = dev.ARC.reset_unit.DEBUG.heartbeat.read()
    heartbeat_0 = arc_read(0x8100786C4)
    delay_seconds = 0.1
    time.sleep(delay_seconds)
    # heartbeat_1 = dev.ARC.ARC_CSM.DEBUG.heartbeat.read()
    heartbeat_1 = arc_read(0x8100786C4)
    if heartbeat_1 <= heartbeat_0:
        print(f"ARC heartbeat not increasing: {RED}{heartbeat_1}{RST}.")
        raiseTTTriageError(check_ARC.__doc__)

    # Compute uptime
    # arcclk_mhz = dev.ARC.ARC_CSM.AICLK_PPM.curr_arcclk.read()
    arcclk_mhz = arc_read(0x8100782AC)
    heartbeats_per_second = (heartbeat_1 - heartbeat_0) / delay_seconds
    uptime_seconds = heartbeat_1 / heartbeats_per_second

    # Heartbeat must be between 500 and 20000 hb/s
    if heartbeats_per_second < 500:
        print(f"ARC heartbeat is too low: {RED}{heartbeats_per_second}{RST}hb/s. Expected at least {BLUE}500{RST}hb/s")
        raiseTTTriageError(check_ARC.__doc__)  
    if heartbeats_per_second > 20000:
        print(f"ARC heartbeat is too high: {RED}{heartbeats_per_second}{RST}hb/s. Expected at most {BLUE}20000{RST}hb/s")
        raiseTTTriageError(check_ARC.__doc__)

    # Print heartbeat and uptime
    verbose(f"ARC heartbeat: {heartbeat_1} - {heartbeat_0} = {heartbeats_per_second}hb/s, ARCCLK: {arcclk_mhz} MHz")
    days = int(uptime_seconds // (24 * 3600))
    hours = int((uptime_seconds % (24 * 3600)) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    verbose(f"Approximate ARC uptime: {GREEN}{days}d {hours:02}:{minutes:02}:{seconds:02}s{RST}")

def check_L1(dev):
    """Checking location 0x0 of each core's L1 for the presence of FW"""
    title(check_L1.__doc__)

    # Firmware loaded L1[0] == 0x3800306f
    addr = 0x0
    expected = 0x7800306f
    for loc in dev.get_block_locations(block_type="functional_workers"):
        data = read_words_from_device(loc, addr, device_id=dev.id(), word_count=1, context=context)
        if data[0] != expected:
            print(f"L1 @{loc}, addr 0x{addr:08x}: {RED}0x{data[0]:08x}{RST}. Expected {BLUE}{expected:08x}{RST}")
            raiseTTTriageError(check_L1.__doc__)

def noc_ping(dev, loc, use_noc1: False):
    data = read_words_from_device(loc, dev.NOC_CONTROL_REGISTER_BASE + dev.NOC_NODE_ID_OFFSET, device_id=dev.id(), word_count=1)
    n_x = data[0] & 0x3F
    n_y = (data[0] >> 6) & 0x3F
    if loc.to('noc0') != (n_x, n_y):
        print(f"loc {RED}{loc.to('noc0')}{RST} Expected {BLUE}({n_x}, {n_y}){RST} but got {RED}{loc.to('noc0')}{RST}")

def check_NOC(dev):
    """Checking that we can reach all NOC endpoints through NOC0 (TODO: NOC1)"""
    title(check_NOC.__doc__)

    # Ping all locations
    for block_type in ["functional_workers", "eth"]:
        verbose (f"Checking {block_type} locations")
        all_locs = dev.get_block_locations(block_type)
        for loc in all_locs:
            noc_ping(dev, loc, use_noc1=False)

def check_riscV(dev: Device):
    """Checking that the RISC-V cores are running. Dumping PC through debug bus (-v)."""
    title(check_riscV.__doc__)

    # RISC-V soft resets are released
        # Reference table for RISC-V core states
        # after tt-smi reset  - after metal run
        # - 0: 0x7fdff7fd     - 0x3fcff3fc  # These vary by device
        # - 1: 0xdff7fdff     - 0xcff3fcff
        # - 2: 0xffffff7f     - 0x0000ff3f
        # - 3: 0xffffffff     - 0x00000000  # These do not vary by device
        # - 4: 0xffffffff     - 0x00000000
        # - 5: 0xffffffff     - 0x00000000
        # - 6: 0xffffffff     - 0x00000000
        # - 7: 0xffffffff     - 0x00000000

    expected_after_metal_run = {
        0: 0x3fcff3fc,
        1: 0xcff3fcff,
        2: 0x0000ff3f,
        3: 0x00000000,
        4: 0x00000000,
        5: 0x00000000,
        6: 0x00000000,
        7: 0x00000000
    }

    # for i in range(len(dev.ARC.ARC_RESET.RISCV_RESET)):
    #     read_value = dev.ARC.ARC_RESET.RISCV_RESET[i].read()
    for i in range(3,8):
        read_value = read_word_from_device(dev.get_arc_block_location(), 0x880030040 + i * 4)

        verbose(f"{i}: 0x{read_value:08x}")
        if read_value != expected_after_metal_run[i]:
            print(f"Mismatch in RiscV reset register {i}: Expected {BLUE}0x{expected_after_metal_run[i]:08x}{RST}, but got {RED}0x{read_value:08x}{RST}")
            raiseTTTriageError("RISC-V core state does not match expected 'after metal run' values.")

    # PC dump through debug bus
    table = []
    header_row = [ "Loc\PC", "brisc_pc", "trisc0_pc", "trisc1_pc", "trisc2_pc", "ncrisc_pc" ]
    table.append(header_row)

    # Dump PC through debug bus
    for loc in dev.get_block_locations(block_type="functional_workers"):
        loc_row = [ f"{loc.to_str('logical')}" ]
        store = dev.get_debug_bus_signal_store(loc)
        for sig in header_row[1:]:
            pc = store.read_signal(sig)
            loc_row.append(f"0x{pc:x}")
        table.append(loc_row)

    verbose(tabulate(table, headers="firstrow", tablefmt=DEFAULT_TABLE_FORMAT))

def dump_running_ops(dev):
    """Print the running operations on the device."""
    title(dump_running_ops.__doc__)

    # Get the running operations
    metal_home = os.environ.get('TT_METAL_HOME')
    if metal_home is None:
        raiseTTTriageError("TT_METAL_HOME is not set. Please set it to the path of the metal directory.")

    runtime_yaml = metal_home + "/generated/silicon_debugger/runtime_data.yaml"
    if not os.path.exists(runtime_yaml):
        raiseTTTriageError(f"Runtime data file {runtime_yaml} does not exist.")

    with open(runtime_yaml, 'r') as f:
        runtime_data = yaml.safe_load(f)

    # Get the location of brisc.elf
    a_kernel_id = list(runtime_data['kernels'].keys())[0]
    a_kernel_path = runtime_data['kernels'][a_kernel_id]['out']
    brisc_elf_path = a_kernel_path + "../../../firmware/brisc/brisc.elf"
    brisc_elf_path = os.path.realpath(brisc_elf_path)
    fw_elf_path = a_kernel_path + "../../../firmware/trisc1/trisc1.elf"
    fw_elf_path = os.path.realpath(fw_elf_path)

    if not os.path.exists(brisc_elf_path):
        raiseTTTriageError(f"BRISC ELF file {brisc_elf_path} does not exist.")
    if not os.path.exists(fw_elf_path):
        raiseTTTriageError(f"FW ELF file {fw_elf_path} does not exist.")

    from ttexalens.parse_elf import read_elf, mem_access
    elf = read_elf(context.server_ifc, brisc_elf_path)

    if not elf:
        raiseTTTriageError(f"Failed to extract DWARF info from ELF file {brisc_elf_path}")
        return
    table = []
    header_row = ["Location", "RD PTR", "Base", "(hex)", "Text Offset", "Text (hex)", "Kernel ID"]
    table.append(header_row)

    for loc in dev.get_block_locations(block_type="functional_workers"):
        def mem_reader(unaligned_addr, size_bytes):
            # As the unaligned_addr does not need to be aligned to 4 bytes, and size_bytes does not need to be a multiple of 4,
            # we need to read the memory in chunks of 4 bytes, and combine the results into an array of dwords

            # Calculate aligned start address and number of words needed
            aligned_addr = (unaligned_addr // 4) * 4
            start_offset = unaligned_addr - aligned_addr
            num_words = (size_bytes + start_offset + 3) // 4  # Round up to nearest word

            # Read the aligned words
            words = read_words_from_device(loc, aligned_addr, device_id=dev.id(), word_count=num_words, context=context)
            if start_offset == 0:
                return words
            else:
                # Convert words to bytes
                bytes_data = b''
                for word in words:
                    bytes_data += word.to_bytes(4, 'little')

                # Extract the requested range
                result = bytes_data[start_offset:start_offset + size_bytes]

                # Convert bytes to words
                words = [int.from_bytes(result[i:i+4], 'little') for i in range(0, len(result), 4)]
                return words

        launch_msg_rd_ptr = mem_access(elf, 'mailboxes->launch_msg_rd_ptr', mem_reader)[0][0]
        ProgrammableCoreTypes_TENSIX = elf["enumerator"]['ProgrammableCoreType::TENSIX'].value # This is how to access the value of an enumerator

        # Refer to tt_metal/api/tt-metalium/dev_msgs.h for struct kernel_config_msg_t
        kernel_config_base = mem_access(elf, f'mailboxes->launch[{launch_msg_rd_ptr}].kernel_config.kernel_config_base[0]', mem_reader)[0][0]  # Indexed with enum ProgrammableCoreType - tt_metal/hw/inc/*/core_config.h
        kernel_text_offset = mem_access(elf, f'mailboxes->launch[{launch_msg_rd_ptr}].kernel_config.kernel_text_offset[3]', mem_reader)[0][0]  # Size 5 (NUM_PROCESSORS_PER_CORE_TYPE) - seems to be DM0,DM1,MATH0,MATH1,MATH2
        watcher_kernel_id  = mem_access(elf, f'mailboxes->launch[{launch_msg_rd_ptr}].kernel_config.watcher_kernel_ids[2]', mem_reader)[0][0] & 0xFFFF
        kernel_name = runtime_data['kernels'][watcher_kernel_id]['src'] if watcher_kernel_id in runtime_data['kernels'] else ""

        row = [
            loc.to_str('logical'),
            str(launch_msg_rd_ptr),
            str(kernel_config_base),
            f"0x{kernel_config_base:08x}",
            str(kernel_text_offset),
            f"0x{kernel_text_offset:08x}",
            str(watcher_kernel_id),
            kernel_name
        ]
        table.append(row)

        # Print callstack for this location using tt_exalens_lib
        if kernel_name:
            kernel_path = runtime_data['kernels'][watcher_kernel_id]['out'] + "trisc1/trisc1.elf"
            if not os.path.exists(kernel_path):
                raiseTTTriageError(f"Kernel ELF file {kernel_path} does not exist.")
            try:
                from ttexalens.tt_exalens_lib import callstack
                print(f"Arguments for callstack: {fw_elf_path}, {kernel_path}, {kernel_config_base + kernel_text_offset}, 2, 100, True, False, {dev.id()}, {context}")
                cs = callstack(loc, [fw_elf_path, kernel_path], [0, kernel_config_base + kernel_text_offset], 2, 100, True, False, dev.id(), context)
                if cs:
                    frame_number_width = len(str(len(cs) - 1))
                    for i, frame in enumerate(cs):
                        print(f"  #{i:<{frame_number_width}} ", end="")
                        if frame.pc is not None:
                            print(f"{BLUE}0x{frame.pc:08X}{RST} in ", end="")
                        if frame.function_name is not None:
                            print(f"{ORANGE}{frame.function_name}{RST} () ", end="")
                        if frame.file is not None:
                            print(f"at {GREEN}{frame.file} {frame.line}:{frame.column}{RST}", end="")
                        print()
                else:
                    print(f"{ORANGE}No callstack available for location {loc.to_str('logical')}{RST}")
            except Exception as e:
                print(f"{RED}Error getting callstack: {e}{RST}")

    print(tabulate(table, headers="firstrow", tablefmt=DEFAULT_TABLE_FORMAT))

def main(argv=None):
    """Main function that runs the triage script."""
    global VERBOSE, VVERBOSE, context, HALT_ON_ERROR
    
    args = docopt(__doc__, argv=argv)
    VERBOSE = args['--verbose']
    VVERBOSE = args['--vverbose']
    HALT_ON_ERROR = args['--halt-on-error']
    set_verbose(VVERBOSE)
    
    context = init_ttexalens(use_noc1=False)
    device_ids = list(context.devices.keys())

    # Pupulate integer array with device ids
    if len(args['--dev']) == 1 and args['--dev'][0].lower() == 'all':
        device_ids = [ int(id) for id in context.devices.keys() ]
    else:
        device_ids = [ int(id) for id in args['--dev'] ]

    verbose(f"Device IDs: {device_ids}")

    try:
        for device_id in device_ids:
            title (f"Checking device {device_id}")
            dev = context.devices[device_id]
            # Check if dev is Wormhole or Blackhole
            if type(dev) == WormholeDevice:
                check_ARC(dev)
                check_NOC(dev)
                check_L1(dev)
                check_riscV(dev)
                dump_running_ops(dev)
            else:
                raiseTTTriageError(f"{dev._arch} devices are not supported yet.")
    except TTTriageError as e:
        print(f"{RED}ERROR: {e}{RST}")
        if args['--halt-on-error']:
            return 1

    print (f"{GREEN}DONE: OK{RST}")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))