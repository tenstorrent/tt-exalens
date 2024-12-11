# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
A module containing utility functions and classes for documentation generation.
"""

from abc import abstractmethod
from typing import List, Dict


def INFO(text: str) -> None:
    print(f"\033[1;32m{text}\033[0m")


def WARNING(text: str) -> None:
    print(f"\033[1;33m{text}\033[0m")


def ERROR(text: str) -> None:
    print(f"\033[1;31m{text}\033[0m")
    raise Exception(text)


class ElementPPrinter:
    def __init__(self):
        """
        A class for pretty printing low-level documentation elements, such as
        text, code, lists, etc.
        """
        pass

    def print_section(self, title: str, content: str, level: int = 3) -> str:
        return f"{'#' * level} {title}\n\n{content}\n\n"

    def print_text(self, text: str) -> str:
        return text.strip() + "\n"

    def print_code(self, code: str) -> str:
        return f"```\n{code}\n```\n"

    def print_items(self, items: List[str]) -> str:
        result = ""
        for item in items:
            result += f"- {item}\n"
        return result

    def print_arg(
        self, argname: str = None, argdesc: str = None, argtype: str = None, optarg: str = None, optshort: str = None
    ) -> str:
        """
        This function can be used for printing arrguments, options, and returns.

        Args:
                argname (str): The name of the argument.
                argdesc (str): The description of the argument.
                argtype (str): The type of the argument.
                optarg (str): The option value.
                optshort (str): The option short name.
        """
        result = f"`{argname}" if argname else ""

        result += f", {optshort}" if optshort else ""
        result += "`" if optshort or argname else ""
        result += f" = **{optarg}**" if optarg else ""

        if type(argtype) == list:
            argtype = ", ".join(argtype)
        result += f" *({argtype})*" if argtype else ""
        result += f": {argdesc}" if argdesc else ""

        return result


"""
DICTIONARY FORMATS FOR PRETTY PRINTING
--------------------------------------

SectionPPrinter class has base methods for printing different sections of the documentation.
On input, they all expect dictionaries made by parsing source code. Although printing should
be done through a derived class, in order to use these base printing methods, the dictionaries
must be properly formatted. Below are the formats for each section.

USAGE:
{
	'code': 'call code text',
}

DESCRIPTION:
{
	'text': 'description text',
}

ARGUMENTS, OPTIONS, ARGS:
# These are all the same format, just different keys. Only the appropriate keys should be used.
{
	'argument/option name': {
		'description': 'arg description',
		'type': 'arg type',
		'arg': 'name of the value that needs to be passed to an option',
		'short': 'short name of an option',
	},
	...
}

EXAMPLES:
{
	'commands': [
		{
			'text': 'command description',
			'code': 'command code',
			'result': 'command result',
		},
		...
	],
}

RETURNS:
{
	'type': 'return type',
	'description': 'return description',
}

NOTES:
{
	'items': [
		'note 1',
		'note 2',
		...
	],
}
"""


class SectionPPrinter:
    def __init__(self, element_printer: ElementPPrinter = ElementPPrinter()):
        """
        A class for pretty printing documentation sections, such as sections, description, arguments, examples, etc.
        """
        self.eprinter = element_printer

    @abstractmethod
    def print_docs(self, docstring: Dict) -> str:
        """
        This abstract method should be implemented in the child class to print the documentation.
        All printing should be done through element_printer to guarantee consistent formatting.
        """
        pass

    def print_usage(self, usage: Dict) -> str:
        return self.eprinter.print_code(usage["code"])

    def print_description(self, description: dict) -> str:
        return self.eprinter.print_text(description["text"])

    def print_arguments(self, arguments: dict) -> str:
        argstrings = []
        for arg, desc in arguments.items():
            argname = arg
            argdesc = desc.get("description", None)
            argtype = desc.get("type", None)

            optarg = desc.get("arg", None)
            optshort = desc.get("short", None)

            argstrings.append(self.eprinter.print_arg(argname, argdesc, argtype, optarg, optshort))

        return self.eprinter.print_items(argstrings)

    def print_examples(self, examples: Dict) -> str:
        result = ""
        for cmd in examples["commands"]:
            result += self.eprinter.print_text(cmd["text"])  # Command description
            result += self.eprinter.print_code(cmd["code"])  # Command call
            if cmd["result"]:  # Command result
                result += self.eprinter.print_text("Output:")
                result += self.eprinter.print_code(cmd["result"])

        return result

    def print_returns(self, returns: dict) -> str:
        return self.eprinter.print_arg(argtype=returns["type"], argdesc=returns["description"])

    def print_notes(self, notes: dict) -> str:
        return self.eprinter.print_items(notes["items"])
