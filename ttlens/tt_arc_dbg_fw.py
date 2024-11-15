# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
# This code is used to interact with the ARC debug firmware on the device.
import os
import time
from typing import Union, List
from ttlens.tt_debuda_context import Context
from ttlens.tt_util import TTException
from ttlens.tt_debuda_lib_utils import check_context, arc_read, arc_write

def arc_dbg_fw_get_buffer_start_addr():
    return 32

NUM_LOG_CALLS_OFFSET = arc_dbg_fw_get_buffer_start_addr() + 7*4

DFW_MSG_CLEAR_DRAM         = 0x1  # Calls dfw_clear_dram(start_addr, size)
DFW_MSG_CHECK_DRAM_CLEARED = 0x2  # Calls dfw_check_dram_cleared(start_addr, size)
DFW_MSG_SETUP_LOGGING      = 0x3  # Calls dfw_setup_log_buffer(start_addr, size)
DFW_MSG_SETUP_PMON         = 0x4  # Calls dfw_setup_pmon(pmon_id, ro_id)

def arc_dbg_fw_send_message(message, arg0: int = 0, arg1: int = 0, device_id: int = 0, context: Context=None) -> None:
    """ Send a message to the ARC debug firmware.
    
    Args:
        message: Message to send. Must be in the lower 8 bits.
        arg0 (int, default 0): First argument to the message.
        arg1 (int, default 0): Second argument to the message.
        device_id (int, default 0): ID number of device to send message to.
        context (Context, optional): Debuda context object used for interaction with device. If None, global context is used and potentially initialized.
    """
    # // Message format in scratch_2:
    # // +-----------+-----------+-----------+-----------+
    # // | 0xab      | 0xcd      | 0xef      | MSG_CODE  |
    # // +-----------+-----------+-----------+-----------+
    # // Message reply in scratch_2:
    # // +-----------+-----------+-----------+-----------+
    # // |         REPLY         | MSG_CODE  | 0x00      |
    # // +-----------+-----------+-----------+-----------+
    context = check_context(context)

    device = context.devices[device_id]
    arc_core_loc = device.get_arc_block_location()    

    arc_write(context, device_id, arc_core_loc, device.get_register_addr("ARC_RESET_SCRATCH3"), arg0)
    arc_write(context, device_id, arc_core_loc, device.get_register_addr("ARC_RESET_SCRATCH4"), arg1)
    assert(message & 0xffffff00 == 0) # "Message must be in the lower 8 bits"
    arc_write(context, device_id, arc_core_loc, device.get_register_addr("ARC_RESET_SCRATCH2"), message | 0xabcdef00)

def arc_dbg_fw_check_msg_loop_running(device_id: int = 0, context: Context = None):
    """
    Send PING, check for PONG
    """
    context = check_context(context)

    device = context.devices[device_id]
    arc_core_loc = device.get_arc_block_location()    

    arc_dbg_fw_send_message(0x88, 0, 0, device_id, context) 
    time.sleep(0.01) # Allow time for reply
    
    reply = arc_read(context, device_id, arc_core_loc, device.get_register_addr("ARC_RESET_SCRATCH2"))
    
    if (reply >> 16) != 0x99 or (reply & 0xff00) != 0x8800: 
        return False
    return True

def arc_dbg_fw_command(command: str, tt_metal_arc_debug_buffer_size: int = 1024, device_id: int = 0, context: Context = None) -> None:
    """
    Send a command to the ARC debug firmware. Available commands are "start", "stop", and "clear":
    """
    if not arc_dbg_fw_check_msg_loop_running(device_id, context):
        raise TTException("ARC debug firmware is not running.")

    DRAM_REGION_START_ADDR = arc_dbg_fw_get_buffer_start_addr()
    
    DRAM_REGION_SIZE = os.getenv("TT_METAL_ARC_DEBUG_BUFFER_SIZE")
    if DRAM_REGION_SIZE is None:
        DRAM_REGION_SIZE = tt_metal_arc_debug_buffer_size
    else:
        DRAM_REGION_SIZE = int(DRAM_REGION_SIZE)

    if command == "start":
        arc_dbg_fw_send_message(DFW_MSG_SETUP_LOGGING, DRAM_REGION_START_ADDR, DRAM_REGION_SIZE, device_id, context)
    elif command == "stop":
        arc_dbg_fw_send_message(DFW_MSG_SETUP_LOGGING, 0xffffffff, 0xffffffff, device_id, context)
    elif command == "clear":
        arc_dbg_fw_send_message(DFW_MSG_SETUP_LOGGING, DFW_MSG_CLEAR_DRAM, DRAM_REGION_SIZE, device_id, context)

def setup_pmon(pmon_id, ro_id, wait_for_l1_trigger, stop_on_flatline, device_id: int = 0, context: Context = None):
    arg0 = pmon_id & 0xff | (ro_id & 0xff) << 8 | (wait_for_l1_trigger & 0xff) << 16 | (stop_on_flatline & 0xff) << 24
    print (f"Setting up PMON {pmon_id}, RO {ro_id}, wait_for_l1_trigger: {wait_for_l1_trigger}, stop_on_flatline: {stop_on_flatline} => {arg0:08x}")
    arc_dbg_fw_send_message(DFW_MSG_SETUP_PMON, arg0, 0, device_id, context)
