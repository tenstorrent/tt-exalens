# SPDX-FileCopyrightText: (c) 2024 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from ttlens.arc_dfw.tt_arc_dbg_fw_log_context import ArcDfwLogContext
from ttlens.tt_util import TTException
from ttlens.tt_lens_context import Context
from ttlens.arc_dfw.logger.tt_arc_logger_fw import ArcDebugLoggerFw
from ttlens.arc_dfw.logger_with_pmon.tt_arc_loggr_with_pmon_code_patcher import ArcDfwLoggerWithPmonCodePatcher
import struct


class ArcDebugLoggerWithPmonFw(ArcDebugLoggerFw):
    def __init__(
        self,
        log_context: ArcDfwLogContext,
        pmon_size: int,
        base_fw_file_path: str = "logger_with_pmon/arc_dfw_logger_with_pmon.hex",
        base_fw_symbols_file_path: str = "logger_with_pmon/arc_dfw_logger_with_pmon.syms",
        modified_fw_file_path: str = "logger_with_pmon/arc_dfw_logger_with_pmon_modified.hex",
        device_id=0,
        context=None,
    ):
        super().__init__(
            log_context, base_fw_file_path, base_fw_symbols_file_path, modified_fw_file_path, device_id, context
        )

        if pmon_size % 8 != 0:
            raise TTException("PMON size must be a multiple of 2")

        self.pmon_size = pmon_size

        self.code_patcher = ArcDfwLoggerWithPmonCodePatcher(
            base_fw_file_path, base_fw_symbols_file_path, modified_fw_file_path, log_context
        )

    def get_number_of_logs(self):
        """
        Get the number of logs.
        """
        return len(self.log_context.log_list) + self.pmon_size // 4

    def setup_pmon(
        self, pmon_id, ro_id, wait_for_l1_trigger, stop_on_flatline, device_id: int = 0, context: Context = None
    ):
        arg0 = (
            pmon_id & 0xFF | (ro_id & 0xFF) << 8 | (wait_for_l1_trigger & 0xFF) << 16 | (stop_on_flatline & 0xFF) << 24
        )
        print(
            f"Setting up PMON {pmon_id}, RO {ro_id}, wait_for_l1_trigger: {wait_for_l1_trigger}, stop_on_flatline: {stop_on_flatline} => {arg0:08x}"
        )
        self.send_message_to_fw(self.DFW_MSG_SETUP_PMON, arg0, 0, device_id, context)

    def _configure_arc_dbg_fw(self):
        super()._configure_arc_dbg_fw()
        self.buffer_header.write_to_field("pmon_size", self.pmon_size, self.device_id, self.context)

    def parse_log_buffer(self, buffer: bytes) -> dict:
        """
        Parses the log buffer and returns the log data.

        Args:
            buffer (bytes): The buffer to parse.

        Returns:
            dict: The log data.
        """
        log_data = {log_info.log_name: [] for log_info in self.log_context.log_list}
        log_data["pmon"] = []
        num_logs = len(self.log_context.log_list)
        num_logs_and_pmons = num_logs + self.pmon_size // 4

        bytees_filled = (
            self.buffer_header.read_from_field("num_log_calls", self.device_id, self.context) * num_logs_and_pmons * 4
        )
        max_nuumber_of_bytes_filled = ((len(buffer) // 4) - (len(buffer) // 4) % num_logs_and_pmons) * 4
        if bytees_filled <= max_nuumber_of_bytes_filled:
            max_nuumber_of_bytes_filled = bytees_filled

        regular_logs_index = 0
        buffer_index = 0
        while buffer_index < len(buffer) and buffer_index < max_nuumber_of_bytes_filled:
            # Skiping the pmon_data
            if regular_logs_index == len(self.log_context.log_list):
                pmons = [
                    struct.unpack("<I", buffer[buffer_index + offset : buffer_index + offset + 4])[0]
                    for offset in range(0, self.pmon_size, 4)
                ]
                log_data["pmon"].append(pmons)
                buffer_index += self.pmon_size
                regular_logs_index = 0
            else:
                value = struct.unpack("<I", buffer[buffer_index : buffer_index + 4])[0]
                log_name = self.log_context.log_list[(buffer_index // 4) % num_logs_and_pmons].log_name
                log_data[log_name].append(
                    self.format_log_by_type(
                        value, self.log_context.log_list[(buffer_index // 4) % num_logs_and_pmons].output
                    )
                )

                regular_logs_index += 1
                buffer_index += 4

        self.sort_log_data(log_data)

        return log_data

    def save_pmons_to_csv(self, log_data: dict, file_path: str):
        """
        Save the PMON data to a CSV file.

        Args:
            log_data (dict): The log data.
            file_path (str): The path to the CSV file.
        """
        with open(file_path, "w") as file:
            file.write("pmon\n")
            for pmon in log_data["pmon"]:
                file.write(",".join([str(pmon_value) for pmon_value in pmon]) + "\n")
