#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.application.current import get_app
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML, fragment_list_to_text, to_formatted_text
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.patch_stdout import patch_stdout
from ttexalens.context import Context
from ttexalens.gdb.gdb_server import GdbServer, ServerSocket
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.tt_exalens_server import TTExaLensServer, start_server


class TTExaLensCompleter(Completer):
    def __init__(self, context: Context):
        self.commands = [cmd["long"] for cmd in context.commands] + [cmd["short"] for cmd in context.commands]
        self.context = context

    # Given a piece of a command, find all possible completions
    def lookup_commands(self, cmd):
        completions = []
        for command in self.commands:
            if command.startswith(cmd):
                completions.append(command)
        return completions

    def fuzzy_lookup_addresses(self, addr):
        completions = self.context.elf.fuzzy_find_multiple(addr, limit=30)
        return completions

    def get_completions(self, document, complete_event):
        if complete_event.completion_requested:
            prompt_current_word = document.get_word_before_cursor(pattern=self.context.elf.name_word_pattern)
            prompt_text = document.text_before_cursor
            # 1. If it is the first word, complete with the list of commands (lookup_commands)
            if " " not in prompt_text:
                for command in self.lookup_commands(prompt_current_word):
                    yield Completion(command, start_position=-len(prompt_current_word))
            # 2. If the currently-edited word starts with @, complete with address lookup from FW (fuzzy_lookup_addresses)
            elif prompt_current_word.startswith("@"):
                addr_part = prompt_current_word[1:]
                for address in self.fuzzy_lookup_addresses(addr_part):
                    yield Completion(f"@{address}", start_position=-len(prompt_current_word))


class SimplePromptSession:
    def __init__(self):
        self.history = InMemoryHistory()

    def prompt(self, message):
        print(fragment_list_to_text(to_formatted_text(message)))
        s = input()
        self.history.append_string(s)
        return s


class UIState:
    def __init__(self, context: Context) -> None:
        self.context = context
        current_device_id = context.device_ids[0]
        assert isinstance(current_device_id, int)
        self.current_device_id: int = current_device_id  # Currently selected device id
        self.current_location = OnChipCoordinate.create("0,0", self.current_device)  # Currently selected core
        self.current_prompt = ""  # Based on the current x,y
        self.gdb_server: GdbServer | None = None
        self.ttexalens_server: TTExaLensServer | None = None  # TTExaLens server object

        # Create prompt object.
        self.is_prompt_session = sys.stdin.isatty()
        self.prompt_session: PromptSession | SimplePromptSession = (
            PromptSession(completer=TTExaLensCompleter(context)) if self.is_prompt_session else SimplePromptSession()
        )

    @property
    def current_device(self):
        return self.context.devices[self.current_device_id]

    def prompt(self, get_dynamic_prompt: Callable[[], HTML]) -> str:
        if self.is_prompt_session:
            with patch_stdout():
                return self.prompt_session.prompt(get_dynamic_prompt)
        else:
            return self.prompt_session.prompt(get_dynamic_prompt())

    def __on_gdb_connection_change(self):
        if self.is_prompt_session:
            app = get_app()
            app.invalidate()

    def start_gdb(self, port: int):
        if self.gdb_server is not None:
            self.gdb_server.stop()
        server = ServerSocket(port)
        server.start()
        self.gdb_server = GdbServer(self.context, server)
        self.gdb_server.on_connected = self.__on_gdb_connection_change
        self.gdb_server.on_disconnected = self.__on_gdb_connection_change
        self.gdb_server.start()

    def stop_gdb(self):
        if self.gdb_server is not None:
            self.gdb_server.stop()
        self.gdb_server = None

    def start_server(self, port: int | None = None):
        if self.ttexalens_server is not None:
            self.ttexalens_server.stop()
        if port is None:
            port = 5555
        self.ttexalens_server = start_server(port, self.context.server_ifc)

    def stop_server(self):
        if self.ttexalens_server is not None:
            self.ttexalens_server.stop()
        self.ttexalens_server = None
