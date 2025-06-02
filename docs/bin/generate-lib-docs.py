#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  generate-lib-docs <input> <output_file> [-a]
  generate-lib-docs <input> [-i]
  generate-lib-docs (-h | --help)

Arguments:
  <input>			Directory containing library files to parse, or a single command file to parse.
					If a directory is provided, __all__ variable from __init__.py will be used to determine which files to parse,
					and if it is not found, all .py files in the directory will be parsed.
  <output_file>		Output .md file to write to. If not provided, the output will be printed to stdout.

Options:
  -a, --append       Append to the output file instead of overwriting it.
  -i, --interactive  Run in interactive mode. Pause after parsing each file.

Description:
  This is a script for automatically generating markdown documentation for TTExaLens library files
  using docstrings of their functions and variables. The script can be run on a single command file or a directory.

Notes:
  The script must be run as a part of the Python package, using syntax like:

    python -m docs.bin.generate-lib-docs <input> <output_file> [-a]

  Following rules are imposed on a docstring for parser to work correctly:
  - Each section should be separated by a blank line.
  - The first paragraph of the docstring should be the description, without a sectio header.
  - The first line of each subsequent section should be the section name followed by a colon.
  - Arguments should be in the form of argname (argtype): argdescription.
  - Return values should be in the form of returntype: returndescription.
  - Notes should be specified as a list, where each new item starts with a dash (-).
"""

import ast
import importlib
import os, sys
import re

from docopt import docopt
from .doc_utils import INFO, WARNING, ERROR
from .doc_utils import SectionPPrinter

with open("ttexalens/tt_exalens_init.py") as f:
    tree = ast.parse(f.read())


class DocstringParser:
    def __init__(self, sections=None, section_parsers=None):
        """A class to parse docstrings from library functions.

        Args:
                sections (list, optional): List of valid section names in the docstring. If None, defaults to ["Description", "Args", "Returns", "Notes"].
                section_parsers (dict, optional): Dictionary of section names and their corresponding parser functions.
                        If None, defaults to parsers for ["Description", "Args", "Returns", "Notes"].
        """
        if sections:
            self.valid_section_names = sections
        else:
            self.valid_section_names = [
                "Description",
                "Args",
                "Returns",
                "Notes",
            ]
        if section_parsers:
            self.section_parsers = section_parsers
        else:
            self.section_parsers = {
                "Description": self.parse_description,
                "Args": self.parse_args,
                "Returns": self.parse_returns,
                "Notes": self.parse_notes,
            }

    def parse(self, docstring):
        """Parses a docstring into a dictionary of sections."""
        # Sections are separated by blank lines, with potential leading/trailing whitespaces
        sections = [sec.strip() for sec in re.split(r"\n[\s\t]*\n", docstring)]
        result = {}

        # The first section is the description and has no header
        result["Description"] = self.parse_description(sections[0])

        for sec in sections[1:]:
            # First line of each section is the section name
            secname, sec = sec.split("\n", 1)
            secname = secname.strip()[:-1]
            #                remove : at the end

            if secname not in self.valid_section_names:
                WARNING(f"Invalid section name: {secname}. Skipping...")
                continue

            # Call the corresponding parser function for the section
            result[secname] = self.section_parsers[secname](sec)

        return result

    def parse_description(self, help: str) -> dict:
        # Remove leading/trailing whitespaces
        lines = [line.strip() for line in help.split("\n")]
        lines = "\n".join(lines)

        return {"text": lines}

    def parse_args(self, help: str) -> dict:
        result = {}
        lines = [line.strip() for line in help.split("\n")]

        for line in lines:
            # Arguments are separated from their descriptions by a colon (:)
            line = line.split(":", 1)

            if len(line) > 1:
                # We have both argument name and description
                arg = line[0]
                # Argument name is before the first opening parenthesis
                name = arg.split("(")[0].strip()
                # Argument types are inside the parentheses
                types_match = re.findall(r"\((.*?)\)", arg)
                if not types_match:
                    # Docstring didn't match expected "arg (type): description" format.
                    # Skip, or provide a default type.
                    types = [""]
                else:
                    types = types_match[0].split(", ")

                description = line[1]
                # Remove leading/trailing whitespaces
                description = [desc.strip() for desc in description.split("\n")]
                description = "\n".join(description)

                result[name] = {"type": types, "description": description}
            else:
                # This is a continuation of the previous argument's description
                result[name]["description"] += f"\n{line[0].strip()}"

        return result

    def parse_returns(self, help: str) -> dict:
        [name, desc] = help.split(":", 1)

        desc = [line.strip() for line in desc.split("\n")]
        desc = "\n".join(desc)

        return {"type": name.strip(), "description": desc}

    def parse_notes(self, help: str) -> dict:
        lines = [line.strip() for line in help.split("\n")]

        items = []
        for line in lines:
            if line.startswith("- "):
                # Notes are formatted as a list, with each item starting with a dash (-)
                items.append(line[2:].strip())
            else:
                # This is a continuation of the previous note
                items[-1] += f" {line}"

        return {"items": items}


class FileParser:
    def __init__(self, docstring_parser: DocstringParser):
        """A class to parse library files and extract docstrings from functions and variables."""
        self.docstring_parser = docstring_parser

    operator_symbols = {
        ast.Add: "+",
        ast.Sub: "-",
        ast.Mult: "*",
        ast.Div: "/",
        ast.Mod: "%",
        ast.Pow: "**",
        ast.LShift: "<<",
        ast.RShift: ">>",
        ast.BitOr: "|",
        ast.BitXor: "^",
        ast.BitAnd: "&",
        ast.FloorDiv: "//",
    }

    def parse(self, file: os.PathLike):
        if not os.path.exists(file):
            ERROR(f"File {file} not found.")

        with open(file) as f:
            tree = ast.parse(f.read())

        # We keep track of the functions and variables we find in the file
        # At some point we might want to add support for classes
        result = {"functions": [], "variables": [], "classes": []}

        for id, node in enumerate(tree.body):
            if type(node) == ast.FunctionDef:
                parsed = self.parse_function(node)
                if not parsed["docstring"]:
                    WARNING(f"No docstring found for function {parsed['name']} in file {file}. Skipping...")
                    # Functions without docstrings are not added to the documentation
                    continue
                parsed["docs"] = self.docstring_parser.parse(parsed["docstring"])
                result["functions"].append(parsed)

            elif type(node) == ast.AnnAssign:
                if not type(tree.body[id - 1]) == ast.Expr:
                    WARNING(f"No docstring found for variable {node.target.id} in file {file}. Skippning...")
                    # Variables without docstrings are not added to the documentation
                    continue
                parsed = self.parse_variable(node, tree.body[id - 1])
                parsed["docs"] = self.docstring_parser.parse(parsed["docstring"])
                result["variables"].append(parsed)

            elif type(node) == ast.Import or type(node) == ast.ImportFrom or type(node) == ast.Expr:
                # We don't need to do anything with these nodes
                continue

            elif isinstance(node, ast.ClassDef):
                # Get class docstring
                class_docstring = ast.get_docstring(node)
                if class_docstring:
                    INFO(f"Class {node.name} docstring found.")
                    # parse with your docstring_parser
                    parsed_doc = self.docstring_parser.parse(class_docstring)
                else:
                    WARNING(f"No docstring found for class {node.name}.")

                # Now parse methods inside the class
                methods = []
                for class_node in node.body:
                    if isinstance(class_node, ast.FunctionDef):
                        method_info = self.parse_function(class_node)  # same function you have
                        if method_info["docstring"]:
                            method_info["docs"] = self.docstring_parser.parse(method_info["docstring"])
                            methods.append(method_info)

                # Then store it all in the result dict
                result["classes"].append(
                    {
                        "name": node.name,
                        "docstring": class_docstring,
                        "docs": parsed_doc if class_docstring else None,
                        "methods": methods,
                    }
                )

            elif isinstance(node, ast.Assign):
                # Similar to AnnAssign but with no annotation
                INFO(f"Found assignment to {node.targets[0].id} at line {node.lineno}.")
                # ...handle docstring/comment if desired...

            else:
                WARNING(f"Node type {type(node)} at index {id} not implemented. Skipping...")

        return result

    def parse_variable(self, node: ast.AnnAssign, docstring_node: ast.Expr = None):
        """Parses a variable declaration and its docstring."""
        name = node.target.id
        docstring = None
        annotation = node.annotation.id
        value = node.value.value if node.value.value else "None"

        if docstring_node:
            docstring = docstring_node.value.value

        return {"name": name, "docstring": docstring, "annotation": annotation, "value": value}

    def _node_returns_to_string(self, node_returns) -> str:
        if type(node_returns) == ast.Name:
            return node_returns.id
        elif type(node_returns) == ast.Constant:
            return node_returns.value
        elif type(node_returns) == ast.Subscript:
            slice_obj = node_returns.slice
            if isinstance(slice_obj, ast.Tuple):
                # Each element is in slice_obj.elts
                returns = []
                for elt in slice_obj.elts:
                    if isinstance(elt, ast.Name):
                        returns.append(elt.id)
                    elif isinstance(elt, ast.Constant):
                        returns.append(str(elt.value))
                    else:
                        returns.append("Unknown")
                return " | ".join(returns)
            else:
                # For non-tuple slices, check if it’s a Name or Constant
                if isinstance(slice_obj, ast.Name):
                    return slice_obj.id
                elif isinstance(slice_obj, ast.Constant):
                    return str(slice_obj.value)
                else:
                    return "Unknown"
        elif type(node_returns) == ast.Attribute:
            return f"{self._node_returns_to_string(node_returns.value)}.{node_returns.attr}"
        elif type(node_returns) == ast.BinOp:
            operator = self.operator_symbols.get(type(node_returns.op), "(Unknown operator)")
            return f"{self._node_returns_to_string(node_returns.left)} {operator} {self._node_returns_to_string(node_returns.right)}"
        elif node_returns is None:
            return "None"
        else:
            raise TypeError(f"Parsing for type {type(node_returns)} not implemented.")

    def parse_function(self, node: ast.FunctionDef):
        """Parses a function definition and its docstring."""
        name = node.name
        args = node.args.args
        defaults = node.args.defaults
        docstring = ast.get_docstring(node)

        returns_string = self._node_returns_to_string(node.returns)

        argstring = ""
        # going backwards, first parse arguments with default values...
        for i in range(-1, -len(defaults) - 1, -1):
            argstring = f"{args[i].arg}={defaults[i].value}, " + argstring
        # and then arguments without default values
        for i in range(-len(defaults) - 1, -len(args) - 1, -1):
            argstring = f"{args[i].arg}, " + argstring

        return {"name": f"{name}", "call": f"{name}({argstring[:-2]}) -> {returns_string}", "docstring": docstring}
        # remove trailing ", "


class LibPPrinter(SectionPPrinter):
    def __init__(self):
        """A class to print library documentation in markdown format."""
        super().__init__()
        self.section_printers = {
            "Description": self.print_description,
            "Args": self.print_arguments,
            "Returns": self.print_returns,
            "Notes": self.print_notes,
        }

    def print_docs(self, docstring: dict) -> str:
        result = ""

        result += self.print_variables(docstring.get("variables", []))
        result += self.print_functions(docstring.get("functions", []))
        result += self.print_classes(docstring.get("classes", []))
        return result

    def print_functions(self, functions: list) -> str:
        result = ""
        for func in functions:
            funcresult = self.print_docstring(func["docs"])
            funcresult = self.eprinter.print_code(func["call"]) + "\n\n" + funcresult
            funcresult = self.eprinter.print_section(func["name"], funcresult, 2)
            result += funcresult
        return result

    def print_variables(self, variables: list) -> str:
        result = ""
        for var in variables:
            varresult = self.print_docstring(var["docs"])
            varresult = (
                self.eprinter.print_arg(
                    argname=var.get("name", None), argtype=var.get("annotation", None), optarg=var.get("value", None)
                )
                + "\n\n"
                + varresult
            )
            varresult = self.eprinter.print_section(var["name"], varresult, 2)

            result += varresult

        return result

    def print_docstring(self, docstring: dict) -> str:
        result = ""
        for sec in self.section_printers.keys():
            if sec in docstring.keys():
                result += self.eprinter.print_section(sec, self.section_printers[sec](docstring[sec]))
        return result

    def print_classes(self, classes: list) -> str:
        """
        Print documentation for a list of classes and their methods.
        """
        result = ""
        for cls in classes:
            # Print class name as a section
            result += self.eprinter.print_section(cls["name"], "", level=2)

            # If there’s a docstring or docs section
            if cls.get("docs"):
                # For example, if you stored the class docstring in 'Description'
                description = cls["docs"].get("Description")
                if description:
                    result += self.print_description(description)

            # Print each method
            for method in cls.get("methods", []):
                method_name = method["name"]
                signature = method["call"]

                # Print method as a sub-section
                result += self.eprinter.print_section(method_name, "", level=3)
                result += self.eprinter.print_code(signature)

                # Print method doc sections
                docs = method.get("docs", {})
                if "Description" in docs:
                    result += self.print_description(docs["Description"])
                if "Args" in docs:
                    result += self.print_arguments(docs["Args"])
                if "Returns" in docs:
                    result += self.print_returns(docs["Returns"])
                if "Notes" in docs:
                    result += self.print_notes(docs["Notes"])

        return result


def get_all_files(path: os.PathLike) -> list:
    """Returns a list of .py files specified in the __all__ variable in __init__.py,
    or all .py files in the directory if __init__.py is not found or does not contain __all__."""
    spec = importlib.util.spec_from_file_location("ttexalens", os.path.join(path, "__init__.py"))
    if spec is not None:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        try:
            return [f + ".py" for f in module.__all__]
        except:
            WARNING(f"__all__ not found in {os.path.join(path, '__init.py__')}. Importing all files from folder.")
    else:
        INFO(f"__init__.py not found in {path}. Importing all files from folder.")

    return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.endswith(".py")]


def parse_directory(path: os.PathLike, parser: FileParser, interactive: bool = False) -> dict:
    """Parses all .py files in a directory using the provided parser.

    Args:
            path (os.PathLike): Path to the directory containing the files to parse.
            parser (FileParser): Parser object to use for parsing the files.
            interactive (bool, optional): If True, the user will be prompted before parsing each file.
    """
    files = get_all_files(path)
    result = {}

    for file in files:
        if interactive:
            response = input(f"Process {file}? (Y/n): ")
            if response.lower() != "y" and response.lower() != "yes" and response.lower() != "":
                continue

        INFO(f"Processing {file}")
        process_result = parser.parse(os.path.join(path, file))
        if process_result:
            result[file] = process_result
        else:
            WARNING(f"Failed to process {file}. Skipping...")

    return result


if __name__ == "__main__":
    args = docopt(__doc__)
    isfile = os.path.isfile(args["<input>"])
    isdir = os.path.isdir(args["<input>"])

    fp = FileParser(DocstringParser())
    lp = LibPPrinter()

    if not isfile and not isdir:
        ERROR("Invalid input. Please provide a valid file or directory.")
        sys.exit(1)
    elif isfile:
        parser_result = {os.path.basename(args["<input>"])[:-3]: fp.parse(args["<input>"])}
    elif isdir:
        parser_result = parse_directory(args["<input>"], fp, interactive=args["--interactive"])

    output = ""
    for file in parser_result.keys():
        output += lp.eprinter.print_section(file[:-3], lp.print_docs(parser_result[file]), 1)

    if args["<output_file>"]:
        with open(args["<output_file>"], "a" if args["--append"] else "w") as f:
            f.write(output)
    else:
        print(output)
