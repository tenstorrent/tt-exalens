
import os
import time
from typing import Union, List
from ttlens.tt_lens_context import Context
from ttlens.tt_util import TTException
from ttlens.tt_arc_dbg_fw_log_context import  LogInfo, ArcDfwLogContext, ArcDfwLogContextFromYaml,ArcDfwLogContextFromList
import struct
from ttlens.tt_arc_dbg_fw import (
    arc_dbg_fw_command,
    arc_dbg_fw_get_buffer_size, 
    load_arc_dbg_fw,
    DFW_BUFFER_HEADER_OFFSETS,
    read_arc_dfw_log_buffer,
    read_dfw_buffer_header,
    ArcDebugLoggerFw
)
from ttlens.tt_lens_lib import read_from_device
import csv

def arc_get_logs_from_list(log_names: List[str], device_id: int = 0, context: Context = None) -> None:
    log_context = ArcDfwLogContextFromList(log_names)
    buffer_data = arc_dfw_get_logs(log_context, device_id, context)
    return buffer_data

def save_to_csv(log_data: bytes, save_location: str) -> None:
    
    with open(save_location, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        headers = ["Sample"] + list(log_data.keys())
        writer.writerow(headers)
        for i in range(len(next(iter(log_data.values())))):
            row = [i] + [log_data[log_name][i] for log_name in log_data]
            writer.writerow(row)

# def plot_log_data(log_data: bytes, save_location: str) -> None:
#     import matplotlib.pyplot as plt

#     for log_name, data in log_data.items():
#         plt.figure()
#         plt.plot(data)
#         plt.title(log_name)
#         plt.xlabel('Sample')
#         plt.ylabel('Value')
#         plt.ylim(min(data) - 1, max(data) + 1) 
#         plt.savefig(os.path.join(save_location, f"{log_name}.png"))
#         plt.close()

def parse_buffer(buffer: bytes, log_context: ArcDfwLogContext) -> None:
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

    for i in range(0, len(buffer), 4):
        if i//4 >= (len(buffer)//4)- (len(buffer)//4) % num_logs:
            break;
        value = struct.unpack('<I', buffer[i:i+4])[0]
        log_name = log_context.log_list[(i // 4) % num_logs].log_name
        log_data[log_name].append(format_output(value, log_context.log_list[(i // 4) % num_logs].output))

    # Sort the log data according to "heartbeat"
    if "heartbeat" in log_data:
        sorted_indices = sorted(range(len(log_data["heartbeat"])), key=lambda i: log_data["heartbeat"][i])
        for log_name in log_data:
            log_data[log_name] = [log_data[log_name][i] for i in sorted_indices]

    return log_data

def arc_dfw_get_logs( log_context: ArcDfwLogContext = ArcDfwLogContextFromYaml("default"),
                              device_id: int = 0,
                              context: Context = None) -> None:
    """
    Graph the ARC debug firmware.
    """
    #load_arc_dbg_fw(log_context=log_context, device_id=device_id, context=context)
    arc_dfw = ArcDebugLoggerFw(log_context, device_id=device_id, context=context) 
    arc_dfw.load()

    arc_dbg_fw_command("start", device_id, context)

    start_time = time.time()
    buffer_size = arc_dbg_fw_get_buffer_size() - len(DFW_BUFFER_HEADER_OFFSETS) * 4
    while (t := read_dfw_buffer_header("num_log_calls", device_id, context)*len(log_context.log_list)*4) <= buffer_size:
        continue

    end_time = time.time() 
    print(f"Time taken to fill buffer: {end_time - start_time} seconds")

    arc_dbg_fw_command("stop", device_id, context)

    start_time = time.time()
    buffer = read_arc_dfw_log_buffer(device_id, context)
    end_time = time.time() 
    print(f"Time taken to fill buffer: {end_time - start_time} seconds")

    return parse_buffer(buffer, log_context)

def read_logs_from_csv(csv_file_path: str) -> None:
    import pandas as pd
    df = pd.read_csv(csv_file_path)
    log_data = {}
    for column in df.columns[1:]:
        log_data[column] = df[column].tolist()
    return log_data

# def plot_from_csv(csv_file_path: str) -> None:
#     import pandas as pd
#     import matplotlib.pyplot as plt

#     df = pd.read_csv(csv_file_path)
#     for column in df.columns[1:]:
#         plt.figure()
#         plt.plot(df['Sample'], df[column])
#         plt.title(column)
#         plt.xlabel('Sample')
#         plt.ylabel('Value')
#         plt.ylim(min(df[column]) - 1, max(df[column]) + 1)
#         plt.show()
#         plt.savefig(os.path.join(os.path.dirname(csv_file_path), f"{column}.png"))
#         plt.close()
