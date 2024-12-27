# SPDX-FileCopyrightText: (c) 2024 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from typing import List
from ttlens.arc_dfw.tt_arc_dbg_fw_code_patcher import ArcDfwCodePatcher
from ttlens.arc_dfw.tt_arc_dbg_fw_log_context import ArcDfwLogContext
from ttlens.tt_lens_lib import read_from_device
import struct
from ttlens.arc_dfw.tt_arc_dbg_fw import ArcDebugFw
from ttlens.arc_dfw.logger.tt_arc_loggr_code_patcher import ArcDfwLoggerCodePatcher
import time
import csv


class ArcDebugLoggerFw(ArcDebugFw):
    def __init__(
        self,
        log_context: ArcDfwLogContext,
        base_fw_file_path: str = "logger/arc_dfw_logger.hex",
        base_fw_symbols_file_path: str = "logger/arc_dfw_logger.syms",
        modified_fw_file_path: str = "logger/arc_dfw_logger_modified.hex",
        device_id=0,
        context=None,
    ):
        super().__init__(base_fw_file_path, base_fw_symbols_file_path, modified_fw_file_path, device_id, context)
        self.log_context = log_context

        self.code_patcher = ArcDfwLoggerCodePatcher(
            base_fw_file_path, base_fw_symbols_file_path, modified_fw_file_path, log_context
        )

    def _configure_arc_dbg_fw(self):
        """
        Configures the firmware for logging.
        """
        self.buffer_header.write_to_field(
            "record_size_bytes", 4 * len(self.log_context.log_list), self.device_id, self.context
        )
        self.buffer_header.write_to_field("log_delay", self.log_context.delay, self.device_id, self.context)

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
            * self.get_number_of_logs()
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

    def get_number_of_logs(self):
        """
        Get the number of logs.
        """
        return len(self.log_context.log_list)

    def log_for_time(self, time_in_seconds: float):
        """
        Log for a specified time.

        Args:
            time_in_seconds (float): The time for which to log.
        """
        self.start_logging()
        time.sleep(time_in_seconds)
        self.stop_logging()

    def sort_log_data(self, log_data: dict):
        """
        Sorts the log data according to pivot point.

        Args:
            log_data (dict): The log data which will be modified by this function.
        """
        log_size = self.get_number_of_logs() * 4
        num_log_calls = self.buffer_header.read_from_field("num_log_calls", self.device_id, self.context)
        max_number_of_one_log = self.buffer_header.get_buffer_usable_size_without_header(log_size) // (log_size)
        pivot_point = num_log_calls % max_number_of_one_log

        for log_name in log_data:
            log_data[log_name] = log_data[log_name][pivot_point:] + log_data[log_name][:pivot_point]

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

        bytees_filled = self.buffer_header.read_from_field("num_log_calls", self.device_id, self.context) * num_logs * 4
        max_nuumber_of_bytes_filled = ((len(buffer) // 4) - (len(buffer) // 4) % num_logs) * 4
        if bytees_filled <= max_nuumber_of_bytes_filled:
            max_nuumber_of_bytes_filled = bytees_filled

        for i in range(0, len(buffer), 4):
            if i >= max_nuumber_of_bytes_filled:
                break
            value = struct.unpack("<I", buffer[i : i + 4])[0]
            log_name = self.log_context.log_list[(i // 4) % num_logs].log_name
            log_data[log_name].append(
                self.format_log_by_type(value, self.log_context.log_list[(i // 4) % num_logs].output)
            )

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
        import os

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
