import os
from enum import Enum, IntEnum
from pathlib import Path
from multiprocessing import Process
import time
import sys

from ttexalens import tt_exalens_init
from ttexalens.tt_exalens_lib import (
    TTException,
    load_elf,
    parse_elf,
    read_from_device,
    read_word_from_device,
    convert_coordinate,
    write_to_device,
    write_words_to_device,
    check_context,
    callstack
)
from ttexalens.hardware.risc_debug import CallstackEntry

from ttexalens.coordinate import OnChipCoordinate

class BootMode(Enum):
    BRISC = "brisc"
    TRISC = "trisc"
    EXALENS = "exalens"
    DEFAULT = "default"

class ChipArchitecture(Enum):
    BLACKHOLE = "blackhole"
    WORMHOLE = "wormhole"
    QUASAR = "quasar"

    def __str__(self):
        return self.value

    @classmethod
    def _get_string_to_enum_map(cls):
        if not hasattr(cls, "_cached_string_map"):
            cls._cached_string_map = {
                "blackhole": cls.BLACKHOLE,
                "quasar": cls.QUASAR,
                "wormhole": cls.WORMHOLE,
            }
        return cls._cached_string_map

    @classmethod
    def from_string(cls, arch_str):
        arch_lower = arch_str.lower()
        enum_value = cls._get_string_to_enum_map().get(arch_lower)
        if enum_value is None:
            raise ValueError(f"Unknown architecture: {arch_str}")
        return enum_value

CHIP_DEFAULT_BOOT_MODES = {
    ChipArchitecture.WORMHOLE: BootMode.BRISC,
    ChipArchitecture.BLACKHOLE: BootMode.BRISC,
    ChipArchitecture.QUASAR: BootMode.TRISC,
}

# Cache for chip architecture
_cached_chip_architecture = None


def get_chip_architecture():
    global _cached_chip_architecture

    if _cached_chip_architecture is not None:
        return _cached_chip_architecture

    chip_architecture = os.getenv("CHIP_ARCH")
    if not chip_architecture:
        context = check_context()
        chip_architecture = str(context.devices[0]._arch)
        if chip_architecture == "wormhole_b0":
            chip_architecture = "wormhole"
        os.environ["CHIP_ARCH"] = chip_architecture

    _cached_chip_architecture = ChipArchitecture.from_string(chip_architecture)
    return _cached_chip_architecture

INVALID_CORE = -1
class RiscCore(IntEnum):
    BRISC = INVALID_CORE if get_chip_architecture() == ChipArchitecture.QUASAR else 11
    TRISC0 = 11 if get_chip_architecture() == ChipArchitecture.QUASAR else 12
    TRISC1 = 12 if get_chip_architecture() == ChipArchitecture.QUASAR else 13
    TRISC2 = 13 if get_chip_architecture() == ChipArchitecture.QUASAR else 14
    TRISC3 = 14 if get_chip_architecture() == ChipArchitecture.QUASAR else INVALID_CORE

    def __str__(self):
        return self.name.lower()

ALL_CORES = [core for core in RiscCore if core != INVALID_CORE]

def get_register_store(location="0,0", device_id=0, neo_id=0):
    CHIP_ARCH = get_chip_architecture()
    context = check_context()
    device = context.devices[device_id]
    chip_coordinate = OnChipCoordinate.create(location, device=device)
    noc_block = device.get_block(chip_coordinate)
    if CHIP_ARCH == ChipArchitecture.QUASAR:
        match neo_id:
            case 0:
                register_store = noc_block.neo0.register_store
            case 1:
                register_store = noc_block.neo1.register_store
            case 2:
                register_store = noc_block.neo2.register_store
            case 3:
                register_store = noc_block.neo3.register_store
            case _:
                raise ValueError(f"Invalid neo_id {neo_id} for Quasar architecture")
    else:
        if neo_id != 0:
            raise ValueError(f"Invalid non zero neo_id for non Quasar architecture")
        register_store = noc_block.get_register_store()
    return register_store


def get_soft_reset_mask(cores: list[RiscCore]):
    if INVALID_CORE in cores:
        raise ValueError("Attempting to reset a core that doesn't exist on this chip")
    return sum(1 << core.value for core in cores)


def set_tensix_soft_reset(
    value, cores: list[RiscCore] = ALL_CORES, location="0,0", device_id=0
):
    soft_reset = get_register_store(location, device_id).read_register(
        "RISCV_DEBUG_REG_SOFT_RESET_0"
    )
    if value:
        soft_reset |= get_soft_reset_mask(cores)
    else:
        soft_reset &= ~get_soft_reset_mask(cores)

    get_register_store(location, device_id).write_register(
        "RISCV_DEBUG_REG_SOFT_RESET_0", soft_reset
    )

def reset_mailboxes(location: str = "0,0"):
    """Reset all core mailboxes before each test."""
    reset_value = 0  # Constant - indicates the TRISC kernel run status
    for mailbox in [Mailbox.Packer, Mailbox.Math, Mailbox.Unpacker]:
        write_words_to_device(location=location, addr=mailbox.value, data=reset_value)


TRISC_START_ADDRS = [0x16DFF0, 0x16DFF4, 0x16DFF8]

class Mailbox(Enum):
    Unpacker = 0x19FFC
    Math = 0x19FF8
    Packer = 0x19FF4

def _print_callstack(risc_name: str, callstack: list[CallstackEntry]):
    print(f"====== ASSERT HIT ON RISC CORE {risc_name.upper()} =======")

    LLK_HOME = Path("./tt-llk").absolute()
    print(LLK_HOME)
    TESTS_DIR = LLK_HOME / "tests"

    for idx, entry in enumerate(callstack):
        # Format PC hex like Rust does

        pc = f"0x{entry.pc:016x}" if entry.pc is not None else "0x????????????????"
        file_path = (TESTS_DIR / Path(entry.file)).resolve()

        # first line: idx, pc, function
        print(f"{idx:>4}: {pc} - {entry.function_name}")

        # second line: file, line, column
        print(f"{' '*25}| at {file_path}:{entry.line}:{entry.column}")

def is_assert_hit(risc_name, core_loc="0,0", device_id=0):
    # check if the core is stuck on an EBREAK instruction

    CHIP_ARCH = get_chip_architecture()
    context = check_context()
    device = context.devices[device_id]
    coordinate = convert_coordinate(core_loc, device_id, context)
    block = device.get_block(coordinate)
    risc_debug = block.get_risc_debug(
        risc_name, neo_id=0 if CHIP_ARCH == ChipArchitecture.QUASAR else None
    )

    is_it = True

    try:
        is_it = risc_debug.is_ebreak_hit()
    except:
        soft_reset = get_register_store(core_loc, device_id).read_register(
            "RISCV_DEBUG_REG_SOFT_RESET_0"
        )

        brisc_debug_pc = block.get_risc_debug("BRISC").get_pc()

        crumbs = read_from_device(core_loc, 0x64FF0, 0, 8)
        before = int.from_bytes(crumbs[0:4], byteorder="little")
        after = int.from_bytes(crumbs[4:8], byteorder="little")
        print(
            f"{core_loc} Host-read reset register {hex(soft_reset)} | brisc pc: {hex(brisc_debug_pc)} | before {hex(before)} after {hex(after)}",
            file=sys.stderr,
        )
        raise Exception("WTF handler")

    return is_it

def handle_if_assert_hit(elfs: list[str], core_loc="0,0", device_id=0):
    trisc_cores = [RiscCore.TRISC0, RiscCore.TRISC1, RiscCore.TRISC2]
    assertion_hits = []

    for core in trisc_cores:
        risc_name = str(core)
        if is_assert_hit(risc_name, core_loc=core_loc, device_id=device_id):
            _print_callstack(
                risc_name,
                callstack(core_loc, elfs, risc_name=risc_name, device_id=device_id),
            )
            assertion_hits.append(risc_name)

def run_elfs(location: str = "0,0"):

    CHIP_ARCH = get_chip_architecture()

    boot_mode = CHIP_DEFAULT_BOOT_MODES[CHIP_ARCH]

    if (
        CHIP_ARCH == ChipArchitecture.QUASAR
        and boot_mode != BootMode.TRISC
    ):
        raise ValueError("Quasar only supports TRISC boot mode")

    reset_mailboxes(location)

    # Perform soft reset
    set_tensix_soft_reset(1, location=location)
    soft_reset_value = (
        get_register_store(location, 0).read_register(
            "RISCV_DEBUG_REG_SOFT_RESET_0"
        )
        >> 11
    )
    if not soft_reset_value & 0xF == 0xF:
        raise Exception(
            f"Cores are not in reset BEFORE elf load: {bin(soft_reset_value)}"
        )

    
    elfs = [
        str(Path(f"./elf_files/{trisc_name}.elf").absolute())
        for trisc_name in ["unpack", "math", "pack"]
    ]

    for i, elf in enumerate(elfs):
        if CHIP_ARCH == ChipArchitecture.WORMHOLE:
            start_address = load_elf(
                elf_file=elf,
                location=location,
                risc_name=f"trisc{i}",
                neo_id=(
                    0 if CHIP_ARCH == ChipArchitecture.QUASAR else None
                ),
                return_start_address=True,
                verify_write=False,
            )
            write_words_to_device(
                location, TRISC_START_ADDRS[i], [start_address]
            )
        else:
            load_elf(
                elf_file=elf,
                location=location,
                risc_name=f"trisc{i}",
                neo_id=(
                    0 if CHIP_ARCH == ChipArchitecture.QUASAR else None
                ),
                verify_write=False,
            )

    soft_reset_value = (
        get_register_store(location, 0).read_register(
            "RISCV_DEBUG_REG_SOFT_RESET_0"
        )
        >> 11
    )
    if not soft_reset_value & 0xF == 0xF:
        raise Exception(
            f"Cores are not in reset AFTER elf load: {bin(soft_reset_value)}"
        )

    load_elf(
        elf_file=str(
            Path("./elf_files/brisc.elf").absolute()
        ),
        location=location,
        risc_name="brisc",
        verify_write=False,
    )

    RUNTIME_ADDRESS = 0x64000

    with open("./temp_runtimes.bin", "rb") as fp:
        serialised_data = fp.read()
        write_to_device(location, RUNTIME_ADDRESS, serialised_data)

    set_tensix_soft_reset(0, [RiscCore.BRISC], location)

    mailboxes = {Mailbox.Unpacker, Mailbox.Math, Mailbox.Packer}


    start_time = time.time()
    backoff = 0.001  # Initial backoff time in seconds

    timeout = 2
    max_backoff = 2

    completed = set()
    end_time = start_time + timeout
    while time.time() < end_time:
        for mailbox in mailboxes - completed:
            if read_word_from_device(location, mailbox.value) == 1:
                completed.add(mailbox)

        if completed == mailboxes:
            return

        backoff = min(backoff * 2, max_backoff)  # Exponential backoff with a cap

    handle_if_assert_hit(
        elfs,
        core_loc=location,
    )

    trisc_hangs = [mailbox.name for mailbox in (mailboxes - completed)]
    raise TimeoutError(
        f"Timeout reached: waited {timeout} seconds for {', '.join(trisc_hangs)}"
    )

increase_dma_limit = True

def worker(location = "0,0"):
    context = tt_exalens_init.init_ttexalens(use_4B_mode=False)
    if increase_dma_limit:
        context.dma_read_threshold = 2400000
        context.dma_write_threshold = 2400000

    for i in range(1000):
        print(f"{location},  {i}")
        run_elfs(location)

NUM_WORKERS = 1

def main():
    processes = []

    for i in range(NUM_WORKERS):
        row, col = divmod(i, 8)
        proc = Process(target=worker, args=(f"{row},{col}",))
        processes.append(proc)

    for proc in processes:
        proc.start()

    for proc in processes:
        proc.join()

    print("Funnished main")


if __name__ == "__main__":
    main()