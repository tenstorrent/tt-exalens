# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from docopt import DocoptExit, docopt
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.device import Device
from ttexalens.uistate import UIState


class CommandParsingException(Exception):
    """Custom exception to wrap DocoptExit and SystemExit."""

    def __init__(self, original_exception):
        self.original_exception = original_exception
        super().__init__(str(original_exception))  # Optional: Forward the message

    def is_parsing_error(self):
        """If exception is DocoptExit, some parsing error occured"""
        return isinstance(self.original_exception, DocoptExit)

    def is_help_message(self):
        """If exception is SystemExit, h or help command is parsed. It is docopt behavior"""
        return isinstance(self.original_exception, SystemExit)


class tt_docopt:
    """
    This is a wraper to docopt that allows for:
    - The common options to be used in multiple commands
    - Iterating over the values of the common options (for_each)
    """

    @staticmethod
    def device_id_for_each(device_id: int | str | None, context: Context, ui_state: UIState):
        if not device_id:
            device_id = ui_state.current_device_id
            device = context.devices[device_id]
            yield device
        elif device_id == "all":
            for device in context.devices.values():
                yield device
        elif type(device_id) == int:
            yield context.devices[device_id]
        else:
            assert type(device_id) == str
            yield context.devices[int(device_id, 0)]

    @staticmethod
    def loc_for_each(loc_str, context: Context, ui_state: UIState, device: Device):
        if not loc_str:
            yield ui_state.current_location.change_device(device)
        elif loc_str == "all":
            for loc in device.get_block_locations(block_type="functional_workers"):
                yield loc
        elif "/" in loc_str:
            for loc in loc_str.split("/"):
                yield OnChipCoordinate.create(loc, device)
        else:
            yield OnChipCoordinate.create(loc_str, device)

    @staticmethod
    def risc_name_for_each(
        risc_name: str | None, context: Context, ui_state: UIState, device: Device, location: OnChipCoordinate
    ):
        if not risc_name or risc_name == "all":
            try:
                noc_block = device.get_block(location)
                riscs = noc_block.all_riscs
                for risc in riscs:
                    yield risc.risc_location.risc_name
            except:
                pass
        else:
            for name in risc_name.split(","):
                yield name

    # We define command options that apply to more than one command here
    OPTIONS: dict[str, dict] = {
        "--verbose": {
            "short": "-v",
            "description": "Execute command with verbose output. [default: False]",
        },
        "--test": {
            "short": "-t",
            "arg": "",
            "description": "Test mode. [default: False]",
        },
        "--device": {
            "short": "-d",
            "arg": "<device-id>",
            "description": "Device ID. Defaults to the current device.",
            "for_each": device_id_for_each,
        },
        "--loc": {
            "short": "-l",
            "arg": "<loc>",
            "description": "Grid location. Defaults to the current location.",
            "for_each": loc_for_each,
        },
        "--risc": {
            "short": "-r",
            "arg": "<risc-name>",
            "description": "RiscV name (e.g. brisc, triscs0, trisc1, trisc2, ncrisc, erisc). [default: all]",
            "for_each": risc_name_for_each,
        },
    }

    @staticmethod
    def create_docopt_options_string(option_names):
        """
        Given an argument name or an iterable over names, return an "Options" string for that argument.
        """
        if not option_names:
            return ""
        if type(option_names) == str:
            option_names = [option_names]

        options_string = ""
        for opt_name in option_names:
            if opt_name not in tt_docopt.OPTIONS:
                raise ValueError(f"Invalid argument name: {opt_name}")
            opt_info = tt_docopt.OPTIONS[opt_name]
            if "arg" in opt_info and opt_info["arg"]:
                arg = f" {opt_info['arg']}"
            else:
                arg = ""
            combined_option = f"{opt_info['short']}{arg}"
            options_string += f"  {combined_option: <20}   {opt_info['description']}\n"
        return options_string

    def __init__(self, doc, argv=None, common_option_names=[]):
        additional_options = tt_docopt.create_docopt_options_string(common_option_names)
        self.doc = doc + f"\nOptions:\n{additional_options}"
        self.argv = argv
        self.option_names = common_option_names
        try:
            self.args = docopt(self.doc, self.argv)
        except (DocoptExit, SystemExit) as e:
            raise CommandParsingException(e)

    def for_each(self, option_name, context: Context, ui_state: UIState, **kwargs):
        option_short_name = tt_docopt.OPTIONS[option_name]["short"]
        opt_value = self.args[option_short_name]
        func = tt_docopt.OPTIONS[option_name]["for_each"]
        yield from func(opt_value, context, ui_state, **kwargs)


def find_command(commands, name):
    for c in commands:
        if c["long"] == name or c["short"] == name:
            return c
    return None
