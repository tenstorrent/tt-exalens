# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0
"""
Rich Formatting API for Tenstorrent ExaLens CLI

This module provides shared formatting utilities for CLI commands using the Rich library.
It enables consistent display of structured data, tables, and other rich output across
different CLI commands.

Data Format Requirements:
    This formatter expects data in specific formats:

    1. For key-value tables (display_key_value_table):
       A flat dictionary where keys are strings and values can be any type:
       {
           "key1": value1,
           "key2": value2,
           ...
       }

    2. For grouped data (display_grouped_data):
       A nested dictionary structure where:
       - The top level keys are group names
       - Each group contains a dictionary of key-value pairs
       {
           "Group1": {
               "key1": value1,
               "key2": value2
           },
           "Group2": {
               "key3": value3,
               "key4": value4
           }
       }

    3. For advanced formatting (using format_value):
       Values can be dictionaries with formatting instructions:
       {
           "format": "hex"|"binary"|"state",  # Format type
           "value": actual_value,             # The raw value
           "description": "Optional text"     # For state types
       }

    4. For specifying table layouts:
       The grouping parameter for display_grouped_data specifies which
       groups should appear side-by-side. It's a list of lists, where:
       - Each inner list defines groups to display in one row
       - Groups within a row are shown side-by-side
       [
           ["Group1", "Group2"],  # These groups appear side-by-side
           ["Group3"]             # This group appears in a new row
       ]

Examples:
    # Basic key-value table display
    from ttexalens.rich_formatters import formatter, console

    # Simple status data
    status_data = {
        "Device ID": 3,
        "Status": "Running",
        "Temperature": 42.5,
        "Clock": 800000000
    }

    # Display as a key-value table
    formatter.display_key_value_table("Device Status", status_data)

    # Displaying grouped data (like register groups)
    grouped_data = {
        "Group A": {
            "field1": 0x1234,
            "field2": 0xABCD,
            "status": "Active"
        },
        "Group B": {
            "counter1": 42,
            "counter2": 123,
            "enabled": True
        }
    }

    # Define display layout (side-by-side groups)
    grouping = [["Group A", "Group B"]]

    # Display the grouped data
    formatter.display_grouped_data(grouped_data, grouping)

    # For simpler output use simple_print=True
    formatter.display_grouped_data(grouped_data, grouping, simple_print=True)

    # Using heading and device info
    formatter.print_device_header(device, location)
    formatter.print_section_header("Configuration Settings")

    # Using Rich formatting in console messages
    console.print("[bold red]Warning:[/bold red] Temperature exceeds threshold")
"""

from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box
from rich.rule import Rule

# Shared console instance that commands can use
console = Console()


class RichFormatter:
    """
    Utility class for formatting and displaying structured data using Rich.
    Provides a reusable API for CLI commands to display data in a consistent way.

    This formatter can handle any hierarchical data structure where data is organized into
    groups and key-value pairs.
    """

    def create_data_table(
        self,
        group_name: str,
        data: Dict[str, Any],
        simple_print: bool = False,
        title_style: str = "bold magenta",
        key_style: str = "cyan",
        value_style: str = "green",
    ) -> Table:
        """
        Creates a Rich Table for a given group of data.

        Args:
            group_name: Name of the data group
            data: Dictionary of keys and values
            simple_print: Whether to use simplified output format
            title_style: Style for the table title
            key_style: Style for the key column
            value_style: Style for the value column

        Returns:
            Rich Table object for display
        """
        table = Table(title=group_name, title_style=title_style)
        if simple_print:
            table.box = box.SIMPLE
            table.show_header = False
        else:
            table.box = box.ROUNDED
            table.show_header = True

        table.add_column("Description", style=key_style, no_wrap=True)
        table.add_column("Value", style=value_style)

        for key, value in data.items():
            if isinstance(value, dict):
                # For structured values
                formatted_value = self.format_value(value)
            elif isinstance(value, int):
                # For integer values, show both hex and decimal
                formatted_value = f"0x{value:08x} ({value:d})"
            else:
                # For other types
                formatted_value = str(value)

            table.add_row(str(key), formatted_value)
        return table

    def format_value(self, value_info: Dict[str, Any]) -> str:
        """
        Format a value based on its format specification.

        Args:
            value_info: Dictionary containing value and format information

        Returns:
            Formatted string representation of the value
        """
        format_type = value_info.get("format", "")
        raw_value = value_info.get("value", "")

        if format_type == "state":
            return value_info.get("description", str(raw_value))
        elif format_type == "hex":
            try:
                int_value = int(raw_value)
                return f"0x{int_value:08x}"
            except Exception:
                return str(raw_value)
        elif format_type == "binary":
            try:
                int_value = int(raw_value)
                return f"0b{int_value:b}"
            except Exception:
                return str(raw_value)
        else:
            return str(raw_value)

    def flatten_grouping(self, grouping: List[List[str]]) -> List[List[str]]:
        """
        Flattens the grouping structure for simple print mode.

        Args:
            grouping: Nested list of group names

        Returns:
            Flattened list where each inner list contains one group name
        """
        flattened = []
        for row in grouping:
            for group in row:
                flattened.append([group])
        return flattened

    def display_grouped_data(
        self,
        data: Dict[str, Dict[str, Any]],
        grouping: List[List[str]],
        simple_print: bool = False,
        empty_text: str = "<No data>",
    ) -> None:
        """
        Display data groups as tables, organized in rows.

        Args:
            data: Dictionary of data groups
            grouping: List of lists specifying how to group tables
            simple_print: Whether to use simplified output format
            empty_text: Text to display when a group has no data
        """
        if simple_print:
            # Transform grouping into single-column format for simple print mode
            grouping = self.flatten_grouping(grouping)

        for group_row in grouping:
            tables: list = []
            for group_name in group_row:
                if group_name in data:
                    tables.append(self.create_data_table(group_name, data[group_name], simple_print))
                else:
                    tables.append(Panel(empty_text, title=group_name))
            console.print(Columns(tables, equal=True, expand=False))
            console.print()  # blank line

    def display_key_value_table(
        self,
        title: str,
        key_values: Dict[str, Any],
        simple_print: bool = False,
        key_col_name: str = "Parameter",
        value_col_name: str = "Value",
        key_style: str = "cyan",
        value_style: str = "green",
        title_style: str = "bold magenta",
    ) -> None:
        """
        Display a simple key-value table.

        Args:
            title: Table title
            key_values: Dictionary of key-value pairs to display
            simple_print: Whether to use simplified output format
            key_col_name: Name for the key column
            value_col_name: Name for the value column
            key_style: Style for the key column
            value_style: Style for the value column
            title_style: Style for the table title
        """
        table = Table(title=title, title_style=title_style)

        if simple_print:
            table.box = box.SIMPLE
            table.show_header = False
        else:
            table.box = box.ROUNDED
            table.show_header = True

        table.add_column(key_col_name, style=key_style)
        table.add_column(value_col_name, style=value_style)

        for key, value in key_values.items():
            if isinstance(value, int):
                formatted_value = f"0x{value:08x} ({value:d})"
            else:
                formatted_value = str(value)

            table.add_row(str(key), formatted_value)

        console.print(table)
        console.print()  # blank line

    #
    # Header and Section Formatting
    #

    def print_device_header(self, device, location, location_format: str = "noc0", style: str = "bold green") -> None:
        """
        Print a standardized device and location header.

        Args:
            device: Device object with id() method
            location: Location object with to_str() method
            location_format: Format string for location.to_str()
            style: Rich style string for the header
        """
        console.print(f"[{style}]==== Device {device.id()} - Location: {location.to_str(location_format)}[/{style}]")

    def print_section_header(
        self, title: str, style: str = "bold blue", line_style: str = "dim", line_char: str = "="
    ) -> None:
        """
        Print a section header with optional separating lines.

        Args:
            title: Header title text
            style: Rich style string for the title
            line_style: Rich style for separator lines
            line_char: Character to use for separator lines
        """
        console.print()
        console.print(f"[{style}]{title}[/{style}]")
        console.print(f"[{line_style}]{line_char * len(title)}[/{line_style}]")

    def print_header(self, text: str, style: str = "bold", line: bool = False, line_char: str = "─") -> None:
        """
        Print a general header text with optional separator line.

        Args:
            text: Header text
            style: Rich style string for the header
            line: Whether to show a separator line
            line_char: Character to use for separator line
        """
        console.print(f"[{style}]{text}[/{style}]")
        if line:
            console.print(Rule(style=style, characters=line_char))


# Create a singleton instance that can be imported by other modules
formatter = RichFormatter()
