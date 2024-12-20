# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
# This code is used to interact with the ARC debug firmware on the device.
import os
import time
from typing import Union, List
from ttlens.tt_lens_context import Context
from ttlens.tt_util import TTException
from ttlens.tt_lens_lib_utils import check_context, arc_read, arc_write, split_32bit_to_16bit
from ttlens.tt_lens_lib import arc_msg, read_words_from_device, read_from_device
from ttlens.tt_arc import load_arc_fw
from ttlens.tt_arc_dbg_fw_log_context import ArcDfwLogContext
from functools import lru_cache
from ttlens.tt_arc_dbg_fw_compiler import ArcDfwLoggerCompiler,ArcDfwLoggerWithPmonCompiler
from abc import abstractmethod, ABC
import struct
import csv


class ArcDfwHeader:

    DFW_BUFFER_HEADER_OFFSETS = {
        "magic_marker": 0,
        "version": 4,
        "status": 8,
        "error": 12,
        "circular_buffer_size_bytes": 16,
        "circular_buffer_start_offset": 20,
        "record_size_bytes": 24,
        "num_log_calls": 28,
        "msg": 32,
        "msg_arg0": 36,
        "msg_arg1": 40,
        "pmon_size": 44,
    }

    DFW_DEFAULT_BUFFER_ADDR = 32

    def write_to_field(self, field: str, value: int, device_id: int, context: Context = None) -> None:
        """
        Modifies the specified field in the DFW buffer header.

        Args:
            field (str): The field to modify.
            value (int): The value to set.
            device_id (int): The ID of the device.
            context (Context): The context in which the device operates. Defaults to None.

        Raises:
            TTException: If the field is invalid or if the value is invalid.
        """
        if field not in self.DFW_BUFFER_HEADER_OFFSETS:
            raise TTException("Invalid field")

        context = check_context(context)
        device = context.devices[device_id]
        arc_core_loc = device.get_arc_block_location()

        dfw_buffer_addr = self.get_buffer_start_addr(device_id, context)

        arc_write(context, device_id, arc_core_loc, dfw_buffer_addr + self.DFW_BUFFER_HEADER_OFFSETS[field], value)

    def read_from_field(self, field: str, device_id: int, context: Context = None) -> int:
        """
        Reads the specified field in the DFW buffer header.

        Args:
            field (str): The field to read.
            device_id (int): The ID of the device.
            context (Context): The context in which the device operates. Defaults to None.

        Returns:
            int: The value of the specified field.

        Raises:
            TTException: If the field is invalid.
        """
        if field not in self.DFW_BUFFER_HEADER_OFFSETS:
            raise TTException("Invalid field")
        context = check_context(context)
        device = context.devices[device_id]
        arc_core_loc = device.get_arc_block_location()

        dfw_buffer_addr = self.get_buffer_start_addr(device_id, context)

        return arc_read(context, device_id, arc_core_loc, dfw_buffer_addr + self.DFW_BUFFER_HEADER_OFFSETS[field])

    def send_buffer_addr_and_size_to_arc_dbg_fw(self, device_id: int, context: Context = None) -> None:
        """
        Sends the buffer address and size to the ARC debug firmware.
        This function sends the default buffer address and the buffer size to the ARC debug firmware using arc_msg.
        Arc needs to have updated firmware to support this feature.

        Args:
            device_id (int): The ID of the device to which the message is sent.
            context (Any): The context in which the message is sent.

        Raises:
            TTException: If the ARC firmware does not support this feature or if there is an error in sending the message.
        """
        MSG_TYPE_ARC_DBG_FW_DRAM_BUFFER_ADDR = 0xAA91
        MSG_TYPE_ARC_DBG_FW_DRAM_BUFFER_SIZE = 0xAA92
        timeout = 1000

        arg0, arg1 = split_32bit_to_16bit(self.DFW_DEFAULT_BUFFER_ADDR)
        response = arc_msg(device_id, MSG_TYPE_ARC_DBG_FW_DRAM_BUFFER_ADDR, True, arg0, arg1, timeout, context)

        if response[0] == -1:
            raise TTException("Newer version of ARC firmware required to support this feature")

        buffer_size = self.get_buffer_size()
        arg0, arg1 = split_32bit_to_16bit(buffer_size)
        response = arc_msg(device_id, MSG_TYPE_ARC_DBG_FW_DRAM_BUFFER_SIZE, True, arg0, arg1, timeout, context)

        if response[0] == -1:
            raise TTException("Arc msg error")

    def get_buffer_start_addr(self, device_id: int = 0, context: Context = None) -> int:
        """
        Retrieves the start address of the debug buffer for the specified device.
        This function checks if the tt-metal is running and has allocated a buffer in the DRAM.
        If so, it returns the address where the buffer is stored. If tt-metal is not running,
        it uses a default address and sends the message to the debug buffer with the default
        address and size.

        Args:
            device_id (int): The ID of the device. Defaults to 0.
            context (Context): The context in which the device operates. Defaults to None.

        Returns:
            int: The start address of the debug buffer.
        """

        context = check_context(context)

        device = context.devices[device_id]

        # If tt-metal is running, it will alocate a buffer in the dram and give us the address where the buffer is stored
        mcore_buffer_addr = arc_read(
            context, device_id, device.get_arc_block_location(), device.get_register_addr("ARC_MCORE_DBG_BUFFER_ADDR")
        )

        if mcore_buffer_addr != 0:
            return mcore_buffer_addr

        # if mccore_buffer_addr is 0, then tt-metal is not running, so we will use the default address, and send the message to the debug buffer
        # with the default address and size
        try:
            self.send_buffer_addr_and_size_to_arc_dbg_fw(device_id, context)
        except TTException as e:
            # This is the mitagation where the device does not have the required firmware to support the feature
            print(str(e) + " Using default buffer address and size.")
            arc_write(
                context,
                device_id,
                device.get_arc_block_location(),
                device.get_register_addr("ARC_MCORE_DBG_BUFFER_ADDR"),
                self.DFW_DEFAULT_BUFFER_ADDR,
            )
            arc_write(
                context,
                device_id,
                device.get_arc_block_location(),
                device.get_register_addr("ARC_MCORE_DBG_BUFFER_SIZE"),
                self.get_buffer_size(),
            )

        return self.DFW_DEFAULT_BUFFER_ADDR

    def get_buffer_size(self) -> int:
        """
        Retrieves the buffer size for ARC debugging from the environment variable.
        This function fetches the value of the environment variable 'TT_METAL_ARC_DEBUG_BUFFER_SIZE',
        converts it to an integer, and returns it. If the environment variable is not set,
        it raises a TTException.

        Returns:
            int: The buffer size for ARC debugging.

        Raises:
            TTException: If the 'TT_METAL_ARC_DEBUG_BUFFER_SIZE' environment variable is not set.
        """

        buffer_size = os.getenv("TT_METAL_ARC_DEBUG_BUFFER_SIZE")

        if buffer_size is None:
            raise TTException("TT_METAL_ARC_DEBUG_BUFFER_SIZE is not set")

        return int(buffer_size)

    def get_header_size(self) -> int:
        return len(self.DFW_BUFFER_HEADER_OFFSETS) * 4

    def get_buffer_size_without_header(self) -> int:
        return self.get_buffer_size() - self.get_header_size()


class ArcDebugFw(ABC):
    def __init__(
        self,
        base_fw_file_path: str,
        base_fw_symbols_file_path: str,
        modified_fw_file_path: str,
        device_id: int = 0,
        context: Context = None,
    ):
        self.base_fw_file_path = base_fw_file_path
        self.base_fw_symbols_file_path = base_fw_symbols_file_path
        self.modified_fw_file_path = modified_fw_file_path
        self.device_id = device_id
        self.compiler = None

        self.context = check_context(context)
        self.buffer_header = ArcDfwHeader()

        file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.base_fw_file_path)

        if not os.path.exists(file_path):
            raise TTException(f"ARC firmwapre file {file_path} does not exist.")

    DFW_MSG_CLEAR_DRAM = 0x1  # Calls dfw_clear_drpam(start_addr, size)
    DFW_MSG_CHECK_DRAM_CLEARED = 0x2  # Calls dfw_check_dram_cleared(start_addr, size)
    DFW_MSG_SETUP_LOGGING = 0x3  # Calls dfw_setup_log_buffer(start_addr, size)
    DFW_MSG_SETUP_PMON = 0x4  # Calls dfw_setup_pmon(pmon_id, ro_id)
    DFW_MSG_RESET_FW = 0x5  # Sends a message to put fw in reset state

    @abstractmethod
    def _configure_arc_dbg_fw(self) -> None:
        pass

    def __prepare_arc_dbg_fw(self) -> None:
        """
        Prepares the ARC debug firmware for logging by sending it a message of the default buffer address and size.

        Args:
            device_id (int): The ID of the device to prepare. Defaults to 0.
            context (Context): The context in which the device operates. Defaults to None.

        Raises:
            TTException: If the ARC debug firmware is not running.
        """
        device = self.context.devices[self.device_id]

        # If tt-metal is running, it will alocate a buffer in the dram and give us the address where the buffer is stored
        mcore_buffer_addr = arc_read(
            self.context,
            self.device_id,
            device.get_arc_block_location(),
            device.get_register_addr("ARC_MCORE_DBG_BUFFER_ADDR"),
        )

        if mcore_buffer_addr == 0:
            # if mccore_buffer_addr is 0, then tt-metal is not running, so we will neet to send the message to the debug buffer
            # with the default address and size, so it can know where to send the messages
            self.buffer_header.send_buffer_addr_and_size_to_arc_dbg_fw(self.device_id, self.context)

    def __reset_if_fw_already_running(self):
        """
        Reset the ARC debug firmware if it is already running.

        Raises:
            TTException: If the ARC debug firmware fails to reset.
        """
        if self.check_msg_loop_running(self.device_id, self.context):
            self.send_command_to_fw("reset", self.device_id, self.context)
            reset_reply = self.read_reply_from_fw(self.device_id, self.context)
            time.sleep(0.01)
            if reset_reply != 1:
                raise TTException("ARC debug firmware failed to reset.")

    def load(self):
        """
        Loads the arc debug firmware onto the chip.
        """
        self.__reset_if_fw_already_running()

        self.compiler.compile()

        self.__prepare_arc_dbg_fw()

        modified_fw_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.modified_fw_file_path)
        load_arc_fw(modified_fw_file_path, 2, self.device_id, self.context)

        reply = self.buffer_header.read_from_field("msg", self.device_id, self.context)
        if reply != 0xBEBACECA:
            raise TTException("ARC debug firmware failed to load, try reseting the card and try again")

        self._configure_arc_dbg_fw()

    def send_message_to_fw(
        self, message, arg0: int = 0, arg1: int = 0, device_id: int = 0, context: Context = None
    ) -> None:
        """Send a message to the ARC debug firmware, using the buffer in the DRAM.

        Args:
            message: Message to send. Must be in the lower 8 bits.
            arg0 (int, default 0): First argument to the message.
            arg1 (int, default 0): Second argument to the message.
            device_id (int, default 0): ID number of device to send message to.
            context (Context, optional): TTLens context object used for interaction with device. If None, global context is used and potentially initialized.
        """
        # // Message format in buffer_header[8]:
        # // +-----------+-----------+-----------+-----------+
        # // | 0xab      | 0xcd      | 0xef      | MSG_CODE  |
        # // +-----------+-----------+-----------+-----------+
        # // Message reply in buffer_header[8]:
        # // +-----------+-----------+-----------+-----------+
        # // |         REPLY         | MSG_CODE  | 0x00      |
        # // +-----------+-----------+-----------+-----------+
        context = check_context(context)

        self.buffer_header.write_to_field("msg_arg0", arg0, device_id, context)
        self.buffer_header.write_to_field("msg_arg1", arg1, device_id, context)
        assert message & 0xFFFFFF00 == 0  # "Message must be in the lower 8 bits"
        self.buffer_header.write_to_field("msg", message | 0xABCDEF00, device_id, context)

    def check_msg_loop_running(self, device_id: int = 0, context: Context = None):
        """
        Send PING, check for PONG
        """
        context = check_context(context)

        self.send_message_to_fw(0x88, 0, 0, device_id, context)
        time.sleep(0.01)  # Allow time for reply

        reply = self.buffer_header.read_from_field("msg", device_id, context)

        if (reply >> 16) != 0x99 or (reply & 0xFF00) != 0x8800:
            return False
        return True

    def read_reply_from_fw(self, device_id: int = 0, context: Context = None) -> int:
        """
        Read the reply from the ARC debug firmware.
        """
        context = check_context(context)

        return self.buffer_header.read_from_field("msg", device_id, context) >> 16

    def send_command_to_fw(self, command: str, device_id: int = 0, context: Context = None) -> None:
        """
        Send a command to the ARC debug firmware. Available commands are "start", "stop", and "clear":
        """
        DRAM_REGION_START_ADDR = self.buffer_header.get_buffer_start_addr(device_id, context)
        DRAM_REGION_SIZE = self.buffer_header.get_buffer_size()

        if command == "start":
            self.send_message_to_fw(
                self.DFW_MSG_SETUP_LOGGING, DRAM_REGION_START_ADDR, DRAM_REGION_SIZE, device_id, context
            )
        elif command == "stop":
            self.send_message_to_fw(self.DFW_MSG_SETUP_LOGGING, 0xFFFFFFFF, 0xFFFFFFFF, device_id, context)
        elif command == "clear":
            self.send_message_to_fw(
                self.DFW_MSG_SETUP_LOGGING, self.DFW_MSG_CLEAR_DRAM, DRAM_REGION_SIZE, device_id, context
            )
        elif command == "reset":
            self.send_message_to_fw(self.DFW_MSG_RESET_FW, 0, 0, device_id, context)

    def read_arc_dfw_log_buffer(self, device_id: int = 0, context: Context = None) -> List[int]:
        """
        Read the log buffer from the ARC debug firmware.

        Args:
            device_id (int): The ID of the device to read the log buffer from.
            context (Context): The context in which the device operates. Defaults to None.

        Returns:
            List[int]: The log buffer.
        """
        buffer_start_addr = (
            self.buffer_header.get_buffer_start_addr(device_id, context) + self.buffer_header.get_header_size()
        )
        buffer_size = self.buffer_header.get_buffer_size() - self.buffer_header.get_header_size()
        return read_from_device("ch0", device_id=device_id, addr=buffer_start_addr, num_bytes=buffer_size)


class ArcDebugLoggerFw(ArcDebugFw):
    def __init__(
        self,
        log_context: ArcDfwLogContext,
        base_fw_file_path: str = "fw/arc/arc_dbg_fw.hex",
        base_fw_symbols_file_path: str = "fw/arc/arc_dbg_fw.syms",
        modified_fw_file_path: str = "fw/arc/arc_modified.hex",
        device_id=0,
        context=None,
    ):
        super().__init__(base_fw_file_path, base_fw_symbols_file_path, modified_fw_file_path, device_id, context)
        self.log_context = log_context

        self.compiler = ArcDfwLoggerCompiler(
            base_fw_file_path, base_fw_symbols_file_path, modified_fw_file_path, log_context
        )

    def _configure_arc_dbg_fw(self):
        """
        Configures the firmware for logging.
        """
        self.buffer_header.write_to_field(
            "record_size_bytes", 4 * len(self.log_context.log_list), self.device_id, self.context
        )

    def start_logging(self) -> None:
        """
        Start logging the ARC debug firmware.
        """
        self.send_command_to_fw("start", self.device_id, self.context)

    def stop_logging(self) -> None:
        """
        Stop logging the ARC debug firmware.
        """
        self.send_command_to_fw("stop", self.device_id, self.context)

    def get_log_buffer(self) -> List[int]:
        """
        Read the log buffer from the ARC debug firmware.

        Args:
            device_id (int): The ID of the device to read the log buffer from.
            context (Context): The context in which the device operates. Defaults to None.

        Returns:
            List[int]: The log buffer.
        """
        buffer_start_addr = (
            self.buffer_header.get_buffer_start_addr(self.device_id, self.context)
            + self.buffer_header.get_header_size()
        )
        buffer_size = self.buffer_header.get_buffer_size_without_header()
        return read_from_device("ch0", device_id=self.device_id, addr=buffer_start_addr, num_bytes=buffer_size)

    def log_until_full_buffer(self):
        """
        Log until the buffer is full.
        """
        self.start_logging()

        buffer_size = self.buffer_header.get_buffer_size_without_header()
        while (
            t := self.buffer_header.read_from_field("num_log_calls", self.device_id, self.context)
            * len(self.log_context.log_list)
            * 4
        ) <= buffer_size:
            continue

        self.stop_logging()

    def get_log_data(self) -> dict:
        """
        Get log data
        """
        buffer = self.get_log_buffer()
        return self.parse_log_buffer(buffer)

    def log_until_full_buffer_and_parse_logs(self) -> dict:
        """
        Logs until the buffer is full and returns parsed logs.
        """
        self.log_until_full_buffer()

        buffer = self.get_log_buffer()

        return self.parse_log_buffer(buffer)


    def format_log_by_type(self, value: int, output_type: str):
        """
        Formats log by its type defined in LogInfo.

        Args:
            value (int): The value to format.
            output_type (str): The type of the log.
        """
        if output_type == "int":
            return int(value)
        elif output_type == "float":
            return struct.unpack("<f", struct.pack("<I", value))[0]
        elif output_type == "float_div_16":  # special case for temperature data
            return struct.unpack("<f", struct.pack("<I", value))[0] / 16
        elif output_type == "hex":
            return value
        else:
            return value

    def sort_log_data(self, log_data: dict):
        """
        Sorts the log data according to "heartbeat".

        Args:
            log_data (dict): The log data which will be modified by this function.
        """
        # Sort the log data according to "heartbeat"
        if "heartbeat" in log_data:
            sorted_indices = sorted(range(len(log_data["heartbeat"])), key=lambda i: log_data["heartbeat"][i])
            for log_name in log_data:
                log_data[log_name] = [log_data[log_name][i] for i in sorted_indices]

    def parse_log_buffer(self, buffer: bytes) -> dict:
        """
        Parses the log buffer and returns the log data.

        Args:
            buffer (bytes): The buffer to parse.

        Returns:
            dict: The log data.
        """
        log_data = {log_info.log_name: [] for log_info in self.log_context.log_list}
        num_logs = len(self.log_context.log_list)

        for i in range(0, len(buffer), 4):
            if i // 4 >= (len(buffer) // 4) - (len(buffer) // 4) % num_logs:
                break
            value = struct.unpack("<I", buffer[i : i + 4])[0]
            log_name = self.log_context.log_list[(i // 4) % num_logs].log_name
            log_data[log_name].append(self.format_log_by_type(value, self.log_context.log_list[(i // 4) % num_logs].output))

        self.sort_log_data(log_data)

        return log_data

    @staticmethod
    def save_log_data_to_csv(log_data: dict, save_location: str) -> None:
        """
        Save log data to a CSV file.

        Args:
            log_data (dict): Dictionary containing log data.
            save_location (str): Location to save the log data.
        """
        with open(save_location, mode="w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            headers = ["Sample"] + list(log_data.keys())
            writer.writerow(headers)
            for i in range(len(next(iter(log_data.values())))):
                row = [i] + [log_data[log_name][i] for log_name in log_data]
                writer.writerow(row)

    @staticmethod
    def read_log_data_from_csv(csv_file_path: str) -> None:
        """
        Read log data from a CSV file.

        Args:
            csv_file_path (str): Path to the CSV file.
        """
        import pandas as pd

        df = pd.read_csv(csv_file_path)
        log_data = {}
        for column in df.columns[1:]:
            log_data[column] = df[column].tolist()
        return log_data

    def save_graph_as_picture(self, log_data: dict, save_location: str):
        """
        Save the graph as a picture.

        Args:
            log_data (dict): Dictionary containing log data.
            save_location (str): Location to save the graph.

        Raises:
            ImportError: If matplotlib is not installed.
        """
        import matplotlib.pyplot as plt
        import numpy as np

        num_logs = len(log_data)
        fig, axes = plt.subplots(num_logs, 1, figsize=(24, 6 * num_logs))
        colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

        for i, (log_name, values) in enumerate(log_data.items()):
            color = colors[i % len(colors)]
            ax = axes[i]
            ax.plot(values, color=color)
            ax.set_title(log_name)
            ax.set_xlabel("Plots")
            ax.set_ylabel("Value")

        plt.tight_layout()
        plt.savefig(save_location)
        plt.close()

    @staticmethod
    def open_graph_in_a_browser(log_data: dict, log_names: List[str], port: int):
        """
        Opens graph in browser using plotly express.

        Args:
            log_data (dict): Dictionary containing log data.
            log_names (List[str]): List of log names to be displayed, None to display all logs.
            port (int): Port number to display the graph.

        Raises:
            ImportError: If plotly is not installed.
        """

        import plotly.express as px
        from http.server import HTTPServer, SimpleHTTPRequestHandler
        import threading

        figures = {}
        for key, data in log_data.items():
            if log_names != None and key == "heartbeat" and "heartbeat" not in log_names:
                continue

            figures[key] = px.line(x=range(len(data)), y=data, title=key.capitalize())

        combined_html = "combined_plots.html"
        with open(combined_html, "w") as f:
            f.write("<html><head><title>Combined Plots</title></head><body>\n")
            for key, fig in figures.items():
                f.write(f"<h1>{key.capitalize()}</h1>\n")
                f.write(
                    fig.to_html(full_html=False, include_plotlyjs="cdn" if key == list(figures.keys())[0] else False)
                )
            f.write("</body></html>")

        httpd = None

        def serve_html():
            nonlocal httpd
            os.chdir(".")
            httpd = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
            print(f"Graph shown at http://localhost:{port}/{combined_html}")
            httpd.serve_forever()

        thread = threading.Thread(target=serve_html, daemon=True)
        thread.start()

        print("Press Enter to stop the server.")
        input()
        print("Server stopped.")
        if httpd:
            httpd.shutdown()
        thread.join()

class ArcDebugLoggerWithPmonFw(ArcDebugLoggerFw):
    def __init__(
        self,
        log_context: ArcDfwLogContext,
        pmon_size: int,
        base_fw_file_path: str = "fw/arc/arc_dbg_fw_pmon.hex",
        base_fw_symbols_file_path: str = "fw/arc/arc_dbg_fw_pmon.syms",
        modified_fw_file_path: str = "fw/arc/arc_modified.hex",
        device_id=0,
        context=None,
    ):
        super().__init__(log_context,base_fw_file_path, base_fw_symbols_file_path, modified_fw_file_path, device_id, context)

        if pmon_size % 8 != 0:
            raise TTException("PMON size must be a multiple of 2")

        self.pmon_size = pmon_size

        self.compiler = ArcDfwLoggerWithPmonCompiler(
            base_fw_file_path, base_fw_symbols_file_path, modified_fw_file_path, log_context
        )
        # self.compiler = ArcDfwLoggerCompiler(
        #     base_fw_file_path, base_fw_symbols_file_path, modified_fw_file_path, log_context
        # )
    
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
        self.buffer_header.write_to_field(
            "pmon_size",self.pmon_size, self.device_id, self.context
        )
    
    def parse_log_buffer(self, buffer: bytes) -> dict:
        """
        Parses the log buffer and returns the log data.

        Args:
            buffer (bytes): The buffer to parse.

        Returns:
            dict: The log data.
        """
        log_data = {log_info.log_name: [] for log_info in self.log_context.log_list}
        num_logs = len(self.log_context.log_list)
        num_logs_and_pmons = num_logs + self.pmon_size // 4
        pmons = []

        j = 0
        i = 0        
        while i<len(buffer):
            # Skiping the pmon_data
            if j == len(self.log_context.log_list):
                for z in range(0, self.pmon_size//4, 4):
                    value = struct.unpack("<I", buffer[i + z : i + z + 4])[0]
                    pmons.append(value)
                i+=self.pmon_size
                j =0

            if i // 4 >= (len(buffer) // 4) - (len(buffer) // 4) % num_logs_and_pmons:
                break
            
            value = struct.unpack("<I", buffer[i : i + 4])[0]
            log_name = self.log_context.log_list[(i // 4) % num_logs_and_pmons].log_name
            log_data[log_name].append(self.format_log_by_type(value, self.log_context.log_list[(i // 4) % num_logs_and_pmons].output))
            
            j+=1
            i+=4

        self.sort_log_data(log_data)

        for i in range(0, len(buffer), 4):
            value = struct.unpack("<I", buffer[i : i + 4])[0]
            print(f"Buffer[{i // 4}]: {value:08x}")

        return log_data