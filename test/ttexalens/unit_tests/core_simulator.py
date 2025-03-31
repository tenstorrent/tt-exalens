# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

from ttexalens import tt_exalens_lib as lib
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.debug_risc import RiscLoader, RiscDebug, RiscLoc, get_register_index, get_risc_id
import time


class RiscvCoreSimulator:
    """Class to simulate and control a RISC-V core for testing purposes."""

    def __init__(self, context: Context, core_desc: str, risc_name: str):
        """Initialize RISC-V core simulator.

        Args:
            context: TTExaLens context
            core_desc: Core description (e.g. "FW0", "FW1")
            risc_name: RISC name (e.g. "BRISC", "TRISC0")
        """
        self.context = context
        self.core_desc = core_desc
        self.risc_name = risc_name
        self.core_loc = self._get_core_location()

        # Initialize core components
        loc = OnChipCoordinate.create(self.core_loc, device=self.context.devices[0])
        self.risc_id = get_risc_id(self.risc_name)
        rloc = RiscLoc(loc, 0, self.risc_id)
        self.rdbg = RiscDebug(rloc, self.context)
        self.loader = RiscLoader(self.rdbg, self.context)

        # Initialize core in reset state
        self.set_reset(True)

        # Set program base address if not already set
        self.program_base_address = self.loader.get_risc_start_address()
        if self.program_base_address is None:
            self.loader.set_risc_start_address(0xD000)
            self.program_base_address = self.loader.get_risc_start_address()

    def _get_core_location(self) -> str:
        """Convert core_desc to core location string."""
        if self.core_desc.startswith("ETH"):
            eth_cores = self.context.devices[0].get_block_locations(block_type="eth")
            core_index = int(self.core_desc[3:])
            if len(eth_cores) > core_index:
                return eth_cores[core_index].to_str()
            raise ValueError(f"ETH core {core_index} not available on this platform")

        elif self.core_desc.startswith("FW"):
            fw_cores = self.context.devices[0].get_block_locations(block_type="functional_workers")
            core_index = int(self.core_desc[2:])
            if len(fw_cores) > core_index:
                return fw_cores[core_index].to_str()
            raise ValueError(f"FW core {core_index} not available on this platform")

        raise ValueError(f"Unknown core description {self.core_desc}")

    def write_program(self, addr: int, data: int):
        """Write program code data at specified address offset."""
        self.write_data_checked(self.program_base_address + addr, data)

    def write_data_checked(self, addr: int, data: int):
        """Write data to memory and verify it was written correctly."""
        lib.write_words_to_device(self.core_loc, addr, data, context=self.context)
        assert self.read_data(addr) == data, f"Data verification failed at address {addr:x}"

    def read_data(self, addr: int) -> int:
        """Read data from memory at specified address."""
        return lib.read_word_from_device(self.core_loc, addr, context=self.context)

    def set_reset(self, reset: bool):
        """Set or clear reset signal."""
        self.rdbg.set_reset_signal(reset)

    def is_in_reset(self) -> bool:
        """Check if core is in reset state."""
        return self.rdbg.is_in_reset()

    def halt(self):
        """Halt core execution."""
        # self.rdbg.enable_debug()
        self.rdbg.halt()

    def continue_execution(self, enable_debug: bool = True):
        """Continue core execution.

        Args:
            enable_debug: Whether to enable debug mode when continuing
        """
        if enable_debug:
            # self.rdbg.enable_debug()
            self.rdbg.cont()
        else:
            self.rdbg.continue_without_debug()

    def step(self):
        """Execute single instruction."""
        self.rdbg.step()

    def get_pc(self) -> int:
        """Get current program counter value from debug bus."""
        return self.get_pc_from_debug_bus()

    def get_pc_from_debug_bus(self) -> int:
        """Get PC value from debug bus."""
        return self.context.devices[0].read_debug_bus_signal(self.core_loc, self.risc_name.lower() + "_pc")

    def is_halted(self) -> bool:
        """Check if core is halted."""
        return self.rdbg.read_status().is_halted

    def is_blackhole(self) -> bool:
        """Check if device is blackhole."""
        return self.context.devices[0]._arch == "blackhole"

    def is_wormhole(self) -> bool:
        """Check if device is wormhole_b0."""
        return self.context.devices[0]._arch == "wormhole_b0"

    def set_branch_prediction(self, enabled: bool):
        """Enable or disable branch prediction."""
        self.loader.set_branch_prediction(enabled)

    def invalidate_instruction_cache(self):
        """Invalidate instruction cache."""
        self.rdbg.invalidate_instruction_cache()

    def get_pc_relative(self) -> int:
        """Get PC value relative to program base address."""
        absolute_pc = self.get_pc()
        return absolute_pc - self.program_base_address if absolute_pc is not None else None

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
        return self.rdbg.read_gpr(reg_num)

    def get_reg_num(self, reg_name: str) -> int:
        """Get register number from name.

        Args:
            reg_name: Register name (e.g. "zero", "ra", "sp", "t0", etc.)

        Returns:
            int: Register number
        """
        return get_register_index(reg_name)
