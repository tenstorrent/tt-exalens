# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  interfaces

Description:
  Shows unique wafer information for devices connected via each interface. Used
  to establish a mapping between the same device on different interfaces.

Examples:
  interfaces             # Shows op mapping for all devices
"""  # Note: Limit the above comment to 100 characters in width


from ttexalens.context import Context
from ttexalens.command_parser import CommandMetadata
from ttexalens.uistate import UIState

command_metadata = CommandMetadata(
    short_name="if",
    long_name="interfaces",
    type="dev",
    description=__doc__,
)


def run(cmd_text: str, context: Context, ui_state: UIState):
    for device_id in context.device_ids:
        device = context.devices[device_id]
        unique_id_str = f"0x{device.unique_id:x}"
        print(f"NOC Device {device_id}: {unique_id_str}")

    for device_id in context.device_ids:
        # mmio chips
        device = context.devices[device_id]
        if device.is_local:
            unique_id_str = f"0x{device.unique_id:x}"
            if device._has_jtag:
                print(f"JTAG Device {device_id}: {unique_id_str}")
            else:
                print(f"PCI Device {device_id}: {unique_id_str}")

    navigation_suggestions: list[int] = []
    return navigation_suggestions
