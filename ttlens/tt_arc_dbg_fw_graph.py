
import os
import time
from typing import Union, List
from ttlens.tt_lens_context import Context
from ttlens.tt_util import TTException
from ttlens.tt_arc_dbg_fw_log_context import  LogInfo, ArcDfwLogContext, ArcDfwLogContextFromYaml
import struct
from ttlens.tt_arc_dbg_fw import arc_dbg_fw_command, arc_dbg_fw_get_buffer_start_addr, arc_dbg_fw_get_buffer_size, DFW_BUFFER_HEADER_OFFSETS
from ttlens.tt_lens_lib import read_words_from_device

def read_arc_dfw_buffer(device_id: int = 0, context: Context = None) -> List[int]:
    buffer_start_addr = arc_dbg_fw_get_buffer_start_addr(device_id, context) + len(DFW_BUFFER_HEADER_OFFSETS) * 4
    buffer_size = arc_dbg_fw_get_buffer_size() - len(DFW_BUFFER_HEADER_OFFSETS) * 4
    return read_words_from_device('ch0', device_id=device_id, addr=buffer_start_addr, word_count=buffer_size//4)

def arc_dbg_fw_graph(log_context: ArcDfwLogContext = ArcDfwLogContextFromYaml("default"), device_id: int = 0, context: Context = None) -> None:
    """
    Graph the ARC debug firmware.
    """
    arc_dbg_fw_command("start", device_id, context)
    time.sleep(0.02)
    arc_dbg_fw_command("stop", device_id, context)
    buffer = read_arc_dfw_buffer(device_id, context)

    import matplotlib.pyplot as plt

    def parse_and_plot_buffer(buffer: List[int], log_context: ArcDfwLogContext, save_location: str) -> None:
        """
        Parses the buffer and plots each log name onto a different graph.

        Args:
            buffer (List[int]): The buffer to parse.
            log_names (List[str]): The names of the logs.
            save_location (str): The location to save the graphs.
        """
        def format_output(value, output_type):
            if output_type == 'int':
                return int(value)
            elif output_type == 'float':
                return struct.unpack('<f', struct.pack('<I', value))[0]
            elif output_type == 'float_div_16': # special case for temperature data
                return struct.unpack('<f', struct.pack('<I', value))[0] / 16
            elif output_type == 'hex':
                return value
            else:
                return value

        log_data = {log_info.log_name: [] for log_info in log_context.log_list}
        num_logs = len(log_context.log_list)

        for i, value in enumerate(buffer):
            if i >= len(buffer)- len(buffer) % num_logs:
                break;
            log_name = log_context.log_list[i % num_logs].log_name
            log_data[log_name].append(format_output(value, log_context.log_list[i % num_logs].output))

        # Sort the log data according to "heartbeat"
        if "heartbeat" in log_data:
            sorted_indices = sorted(range(len(log_data["heartbeat"])), key=lambda i: log_data["heartbeat"][i])
            for log_name in log_data:
                log_data[log_name] = [log_data[log_name][i] for i in sorted_indices]

        for log_name, data in log_data.items():
            plt.figure()
            plt.plot(data)
            plt.title(log_name)
            plt.xlabel('Sample')
            plt.ylabel('Value')
            plt.ylim(min(data) - 1, max(data) + 1)  # Set y-axis scale to be within a range of 10
            plt.savefig(os.path.join(save_location, f"{log_name}.png"))
            plt.close()

    # Example usage:
    save_location = "fw/arc/graph"
    save_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../", save_location)
    parse_and_plot_buffer(buffer, log_context, save_path)
