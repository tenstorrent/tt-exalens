# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

from ttexalens import tt_exalens_lib as lib
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.hardware.baby_risc_debug import BabyRiscDebug, get_register_index


class RiscvCoreSimulator:
    """Class to simulate and control a RISC-V core for testing purposes."""

    program_base_address: int = 0

    def __init__(self, context: Context, core_desc: str, risc_name: str, neo_id: int | None = None):
        """Initialize RISC-V core simulator.

        Args:
            context: TTExaLens context
            core_desc: Core description (e.g. "FW0", "FW1")
            risc_name: RISC name (e.g. "BRISC", "TRISC0")
        """
        self.context = context
        self.device = self.context.devices[0]
        self.core_desc = core_desc
        self.risc_name = risc_name
        self.neo_id = neo_id
        self.core_loc = self._get_core_location()

        # Initialize core components
        self.location = OnChipCoordinate.create(self.core_loc, device=self.device)
        self.noc_block = self.device.get_block(self.location)
        risc_debug = self.noc_block.get_risc_debug(self.risc_name, self.neo_id)
        assert isinstance(risc_debug, BabyRiscDebug), f"Expected BabyRiscDebug instance, got {type(risc_debug)}"
        self.risc_debug: BabyRiscDebug = risc_debug
        assert self.risc_debug.debug_hardware is not None
        self.debug_hardware = self.risc_debug.debug_hardware
        debug_bus = self.noc_block.get_debug_bus(self.neo_id)
        assert debug_bus is not None
        self.debug_bus_store: DebugBusSignalStore = debug_bus
        if self.risc_debug.risc_info.can_change_code_start_address:
            self.risc_debug.risc_info.set_code_start_address(self.risc_debug.register_store, 0xD000)
        self.program_base_address = self.risc_debug.risc_info.get_code_start_address(self.risc_debug.register_store)

        # Initialize core in reset state
        self.set_reset(True)

    def _get_core_location(self) -> str:
        """Convert core_desc to core location string."""
        if self.core_desc.startswith("ETH"):
            eth_blocks = self.device.idle_eth_blocks
            core_index = int(self.core_desc[3:])
            if len(eth_blocks) > core_index:
                return eth_blocks[core_index].location.to_str()
            raise ValueError(f"ETH core {core_index} not available on this platform")

        elif self.core_desc.startswith("FW"):
            fw_cores = self.device.get_block_locations(block_type="functional_workers")
            core_index = int(self.core_desc[2:])
            if len(fw_cores) > core_index:
                return fw_cores[core_index].to_str()
            raise ValueError(f"FW core {core_index} not available on this platform")
        elif self.core_desc.startswith("DRAM"):
            dram_cores = self.device.get_block_locations(block_type="dram")
            core_index = int(self.core_desc[4:])
            if len(dram_cores) > core_index:
                return dram_cores[core_index].to_str()
            raise ValueError(f"DRAM core {core_index} not available on this platform")

        raise ValueError(f"Unknown core description {self.core_desc}")

    def write_program(self, addr: int, data: int | list[int]):
        """Write program code data at specified address offset."""
        self.write_data_checked(self.program_base_address + addr, data)

    def write_data_checked(self, addr: int, data: int | list[int]):
        """Write data to memory and verify it was written correctly."""
        if isinstance(data, int):
            lib.write_words_to_device(self.core_loc, addr, data, context=self.context)
            assert self.read_data(addr) == data, f"Data verification failed at address {addr:x}"
        else:
            byte_data = b"".join(x.to_bytes(4, "little") for x in data)
            lib.write_to_device(self.core_loc, addr, byte_data, context=self.context)
            read_data = lib.read_from_device(self.core_loc, addr, num_bytes=len(byte_data), context=self.context)
            assert read_data == byte_data, f"Data verification failed at address {addr:x}"

    def read_data(self, addr: int) -> int:
        """Read data from memory at specified address."""
        return lib.read_word_from_device(self.core_loc, addr, context=self.context)

    def set_reset(self, reset: bool):
        """Set or clear reset signal."""
        self.risc_debug.set_reset_signal(reset)

    def is_in_reset(self) -> bool:
        """Check if core is in reset state."""
        return self.risc_debug.is_in_reset()

    def halt(self):
        """Halt core execution."""
        self.risc_debug.halt()

    def continue_execution(self, enable_debug: bool = True):
        """Continue core execution.

        Args:
            enable_debug: Whether to enable debug mode when continuing
        """
        if enable_debug:
            self.risc_debug.cont()
        else:
            self.debug_hardware.continue_without_debug()

    def step(self):
        """Execute single instruction."""
        self.risc_debug.step()

    def get_pc(self) -> int:
        """Get current program counter value from debug bus."""
        return self.risc_debug.read_gpr(get_register_index("pc"))

    def get_pc_from_debug_bus(self) -> int:
        """Get PC value from debug bus."""
        return self.debug_bus_store.read_signal(self.risc_name.lower() + "_pc")

    def is_halted(self) -> bool:
        """Check if core is halted."""
        return self.risc_debug.is_halted()

    def is_ebreak_hit(self) -> bool:
        """Check if ebreak instruction was hit."""
        return self.read_status().is_ebreak_hit

    def is_blackhole(self) -> bool:
        """Check if device is blackhole."""
        return self.device._arch == "blackhole"

    def is_wormhole(self) -> bool:
        """Check if device is wormhole_b0."""
        return self.device._arch == "wormhole_b0"

    def is_quasar(self):
        """Check if device is quasar."""
        return self.device._arch == "quasar"

    def is_eth_block(self):
        """Check if the core is ETH."""
        return self.device.get_block_type(self.location) == "eth"

    def set_branch_prediction(self, enabled: bool):
        """Enable or disable branch prediction."""
        self.risc_debug.set_branch_prediction(enabled)

    def invalidate_instruction_cache(self):
        """Invalidate instruction cache."""
        self.risc_debug.invalidate_instruction_cache()

    def get_pc_relative(self) -> int:
        """Get PC value relative to program base address."""
        return self.get_pc() - self.program_base_address

    def get_pc_and_print(self) -> int:
        """Get PC value and print it for debugging."""
        pc = self.get_pc()
        print(f"{self.risc_name} PC: 0x{pc:08x} (relative: 0x{self.get_pc_relative():x})")
        return pc

    def read_gpr(self, reg_num: int) -> int:
        """Read general purpose register value.

        Args:
            reg_num: Register number (0-32)

        Returns:
            int: Register value

        Raises:
            ValueError: If register number is invalid
        """
        if not 0 <= reg_num <= 32:
            raise ValueError(f"Invalid register number {reg_num}. Must be between 0 and 32.")
        return self.risc_debug.read_gpr(reg_num)

    def write_gpr(self, reg_num: int, value: int):
        """Write general purpose register value.

        Args:
            reg_num: Register number (0-32)
            value: Value to write to the register

        Raises:
            ValueError: If register number is invalid
        """
        if not 0 <= reg_num <= 32:
            raise ValueError(f"Invalid register number {reg_num}. Must be between 0 and 32.")
        self.risc_debug.write_gpr(reg_num, value)

    def get_reg_num(self, reg_name: str) -> int:
        """Get register number from name.

        Args:
            reg_name: Register name (e.g. "zero", "ra", "sp", "t0", etc.)

        Returns:
            int: Register number
        """
        return get_register_index(reg_name)

    def read_status(self):
        return self.debug_hardware.read_status()
