# SPDX-FileCopyrightText: (c) 2024 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from ttlens.arc_dfw.logger.tt_arc_loggr_code_patcher import ArcDfwLoggerCodePatcher


class ArcDfwLoggerWithPmonCodePatcher(ArcDfwLoggerCodePatcher):
    def _get_bytes_that_modify_expandable_function(self) -> bytes:
        """
        Adds instructions to log addresses. For each address in log_context it adds a load instruction followed by a store.
        """
        # Adding instructions to log addresses
        instruction_bytes = []
        for i, log_info in enumerate(self.log_context.log_list):
            instruction_bytes += self._create_load_instruction(1, log_info.address)
            instruction_bytes += self._create_store_instruction(0, 1, i)

        # Pushing branch link register to the stack because we need it to return to the main loop
        instruction_bytes += [0xC0, 0xF1]  # push_s blink

        # Adding instructions to jump to function that logs pmon data
        instruction_bytes += [0x20, 0x22, 0x0F, 0x80]  # Instruction to jump to pmon log function
        pmon_log_address = self.symbol_locations["dfw_pmon_log"]
        instruction_bytes += [
            (pmon_log_address >> 24) & 0xFF,
            (pmon_log_address >> 16) & 0xFF,
            (pmon_log_address >> 8) & 0xFF,
            pmon_log_address & 0xFF,
        ]
        instruction_bytes += [0xC0, 0xD1]  # pop_s blink

        # Loading dfw_buffer_header address so it can be incremented
        instruction_bytes += self._create_load_instruction(1, self.symbol_locations["dfw_buffer_header"])
        # Incrementing the number of log calls and returning to the main loop
        # end_address:	     443c                	ld_s	r0,[r1,0x1c]
        # end_address + 0x2: 7104                	add_s	r0,r0,1
        # end_address + 0x4: a107                	st_s	r0,[r1,0x1c]
        # end_address + 0x6: 7ee0                	j_s	[blink]
        instruction_bytes += [0x44, 0x3C, 0x71, 0x04, 0xA1, 0x07, 0x7E, 0xE0]

        return instruction_bytes
