# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  parse-debug-bus-json <json-path> [<groups>] [-d <device>] [-l <loc>]

Arguments:
  <json-path>      Path to json file containing debug bus signal groups.
  <groups>         Comma-separated group names to print. [default: all]

Description:
  Loads json file containing debug bus signal groups and prints group values for the selected device/location.

Examples:
  parse-debug-bus-json ./debug_bus_signal_groups.json
  parse-debug-bus-json ./debug_bus_signal_groups.json brisc_group_a,rwc_status_signals
  parse-debug-bus-json ./debug_bus_signal_groups.json -d 0 -l 0,0
"""

from __future__ import annotations

import json
import tabulate

from ttexalens import util
from ttexalens.context import Context
from ttexalens.device import Device
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.uistate import UIState
from ttexalens.command_parser import CommandMetadata, tt_docopt, CommonCommandOptions

command_metadata = CommandMetadata(
    short_name="parse",
    long_name="parse-debug-bus-json",
    type="low-level",
    description=__doc__,
    common_option_names=[CommonCommandOptions.Device, CommonCommandOptions.Location],
)


def _load_debug_bus_json(json_path: str) -> dict:
    with open(json_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_groups_arg(groups: dict[str, str], groups_arg: str) -> dict[str, str]:
    groups_arg = groups_arg.strip()
    selected_group_names = []
    if not groups_arg or groups_arg.lower() == "all":
        selected_group_names = sorted(groups.keys())
    else:
        for pattern in groups_arg.split(","):
            selected_group_names.extend(util.search(groups.keys(), pattern.strip()))
    return {name: groups[name] for name in sorted(groups.keys()) if name in selected_group_names}


def _get_location_key(loc: OnChipCoordinate) -> str:
    return f"location: {loc.to_user_str()}"


def _render_groups_table(groups: dict[str, str], title: str) -> str:
    rows = [[name, value] for name, value in groups.items()]
    return tabulate.tabulate(
        rows,
        headers=[title, "Value"],
        tablefmt="simple_outline",
        colalign=("left", "left"),
        disable_numparse=True,
    )


def run(cmd_text: str, context: Context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    json_path = dopt.args["<json-path>"]
    groups_arg = dopt.args["<groups>"] or "all"

    try:
        data = _load_debug_bus_json(json_path)
    except Exception as exc:
        util.ERROR(str(exc))
        return []

    device: Device
    for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state):
        device_key = f"Device {device.id}"
        if device_key not in data:
            util.WARN(f"No data found for {device_key}.")
            continue

        loc: OnChipCoordinate
        for loc in dopt.for_each(CommonCommandOptions.Location, context, ui_state, device=device):
            block_type = device.get_block_type(loc) if device.get_block_type(loc) != "functional_workers" else "tensix"
            if block_type not in data[device_key]:
                util.WARN(f"No data found for {block_type} on {device_key}.")
                continue

            loc_key = _get_location_key(loc)
            if loc_key not in data[device_key][block_type]:
                util.WARN(f"No data found for {loc_key} on {device_key}.")
                continue
            loc_data = data[device_key][block_type][loc_key]

            debug_bus_signal_groups = loc_data.get("debug_bus_signal_groups", {})
            if not debug_bus_signal_groups:
                util.WARN(f"No debug_bus_signals found for {device_key} {loc_key}.")
                continue

            selected_groups = _parse_groups_arg(debug_bus_signal_groups, groups_arg)

            if not selected_groups:
                util.WARN(f"No matching groups for {device_key} {loc_key}.")
                continue

            util.INFO(f"Debug bus signals for location {loc.to_user_str()} on device {device.id}")
            print(_render_groups_table(selected_groups, "Group"))

    return []
