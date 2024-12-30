# SPDX-FileCopyrightText: (c) 2024 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from typing import List
from ttlens.arc_dfw.tt_arc_dbg_fw_code_patcher import ArcDfwCodePatcher
from ttlens.arc_dfw.tt_arc_dbg_fw_log_context import ArcDfwLogContext


class ArcDfwLoggerCodePatcher(ArcDfwCodePatcher):
    def __init__(
        self, base_fw_file_path: str, symbols_file_path: str, output_fw_file_path: str, log_context: ArcDfwLogContext
    ):
        super().__init__(base_fw_file_path, symbols_file_path, output_fw_file_path)
        self.log_context = log_context

    def _get_bytes_that_modify_expandable_function(self) -> List[int]:
        """
        Adds instructions to log addresses. For each address in log_context it adds a load instruction followed by a store.
        """
        # Adding instructions to log addresses
        instruction_bytes = []
        for i, log_info in enumerate(self.log_context.log_list):
            instruction_bytes += self._create_load_instruction(1, log_info.address)
            instruction_bytes += self._create_store_instruction(0, 1, i)

        # Loading dfw_buffer_header address so it can be incremented
        instruction_bytes += self._create_load_instruction(1, self.symbol_locations["dfw_buffer_header"])
        # Incrementing the number of log calls and returning to the main loop
        # end_address:	     443c                	ld_s	r0,[r1,0x1c]
        # end_address + 0x2: 7104                	add_s	r0,r0,1
        # end_address + 0x4: a107                	st_s	r0,[r1,0x1c]
        # end_address + 0x6: 7ee0                	j_s	[blink]
        instruction_bytes += [0x44, 0x3C, 0x71, 0x04, 0xA1, 0x07, 0x7E, 0xE0]

        return instruction_bytes
