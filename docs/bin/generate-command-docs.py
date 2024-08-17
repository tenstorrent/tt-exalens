#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  geenrate-command-docs.py <input> <output_file> [-a]
  geenrate-command-docs.py <input> [-i]
  geenrate-command-docs.py (-h | --help)

Arguments:
  <input>			Directory containing command files to parse, or a single command file to parse.
  <output_file>		Output .md file to write to. If not provided, the output will be printed to stdout.

Options:
  -a, --append       Append to the output file instead of overwriting it.
  -i, --interactive  Run in interactive mode. Pause after parsing each file.

Description:
  This is a script for automatically generating markdown documentation for debuda commands
  using their docopt strings. The script can be run on a single command file or a directory.
  If examples are provided in a command's description, the script will run each example and capture its output to add to the documentation.

Note:
  Following rules are imposed on a docstring for parser to work correctly:
  - Each section should be separated by a blank line.
  - The first line of each section should be the section name followed by a colon.
  - Arguments and options should be separated from their descriptions by multiple spaces.
  - Option arguments should be separated from option name by a space or an equal sign.
  - Examples should be in the format: command # description [ # context ], where context part is in the form of "Needs <context> context".
    If the command needs Buda context, it is not run, as Buda output folder is needed for it.
"""
import sys, re, os, importlib
from docopt import docopt

sys.path.insert(0, 
				os.path.abspath(
					os.path.join(
						os.environ['DEBUDA_HOME']
						)
					)
				)

# We need to import common options as they are sometimes injected into the docstrings
from dbd.tt_commands import tt_docopt
OPTIONS = tt_docopt.OPTIONS
for opt in OPTIONS.keys():
	OPTIONS[opt]['arg'] = OPTIONS[opt].get('arg', '').replace("<", "\<").replace(">", "\>")

# We limit what each example can output to avoid spamming the user
MAX_OUTPUT_LINES = 20  # Max number of lines to show for each example
MAX_CHARACTERS_PER_LINE = 130  # Max number of characters to show for each line

from run_debuda_on_help_examples import execute_debuda_command
from doc_utils import SectionPPrinter, INFO, WARNING, ERROR


class CmdParser:
	def __init__(self, valid_sections: list = None, section_parsers: dict = None):
		""" The parser class for debuda command docstrings.

		Args:
		- valid_sections (list): List of valid section names in the docstring.
		- section_parsers (dict): Dictionary of section names and their corresponding parsing functions.
		"""
		if valid_sections:
			self.valid_section_names = valid_sections
		else:
			self.valid_section_names = ["Usage", "Arguments", "Options", "Description", "Examples"]
		
		if section_parsers:
			self.section_parsers = section_parsers
		else:
			self.section_parsers = {
				"Usage": self.parse_usage,
				"Arguments": self.parse_arguments,
				"Options": self.parse_options,
				"Description": self.parse_description,
				"Examples": self.parse_examples
			}

	def parse(self, cmd_doc: str, common_options: list = None) -> dict:
		result = {}

		# We expect each section to be separated by a blank line
		sections = [sec.strip() for sec in cmd_doc.split("\n\n")]
		for sec in sections:
			# First line of each section is the section name
			secname = sec.split("\n")[0].strip()[:-1]
			#                                   remove : at the end

			if secname not in self.valid_section_names:
				WARNING(f"Invalid section name: {secname}. Skipping...")
				continue
			
			# Call the corresponding parser function for the section
			result[secname] = self.section_parsers[secname](sec)

		# Additionaly, some commands may have common options
		if common_options and len(common_options) > 0:
			result['Common options'] = self.parse_common_options(common_options)

		return result

	def parse_usage(self, help: str) -> dict:
		result = {}

		lines = [line.strip() for line in help.split("\n")]
		txt = ""
		# Sometimes, lines are pretty formatted using multiple spaces.
		# We remove them when building the documenation.
		for l in lines[1:]:
			txt += re.sub(r'\s+', ' ', l) + "\n"
		
		# Remove the last newline character
		txt = txt.strip()

		result['code'] = txt

		return result

	def parse_arguments(self, help: str) -> dict:
		result = {}
		lines = [line.strip() for line in help.split("\n")]

		for line in lines[1:]:
			# Arguments are separated from their descriptions by multiple spaces
			line = re.split(r'\s{2,}', line)
			if len(line) > 1:
				# We have both argument and description
				arg = line[0]
				result[arg] = {'description': line[1]}
			else:
				# We only have the description, so we append it to the last argument
				result[arg]['description'] += " " + line[0]

		return result

	def parse_options(self, help: str) -> dict:
		# This function builds an option dictionary akin to one in the tt_commands module
		result = {}
		lines = [line.strip() for line in help.split("\n")]

		# Create a list of strings, where each string is an option with its description
		opt_strings = []
		# The first line is the section name, so we skip it
		for line in lines[1:]:
			if line.startswith("-") or line.startswith("<"):
				# We have a new option
				opt_strings.append(line)
			else:
				# This is just a description, so we append it to the last option
				opt_strings[-1] += " " + line

		for opt in opt_strings:
			# Option strings are separated from their descriptions by multiple spaces
			opt_parts = re.split('\s{2,}', opt)

			# Separate the option name and its argument (if any)
			# Argument is separated by a space or an equal sign
			opt_call = re.split(r'[ =]', opt_parts[0])
			
			# We don't need the brackets if this is an argument
			opt_call[0] = opt_call[0].replace("<", "").replace(">", "")
			result[opt_call[0]] = {}
			# Is there an argument?
			if len(opt_call) > 1:
				# Bracket characters are interpreted as html tags, so we replace them
				result[opt_call[0]]['arg'] = opt_call[1].replace("<", "\<").replace(">", "\>")
			result[opt_call[0]]['description'] = opt_parts[1]
		
		return result
	
	def parse_description(self, help: str) -> dict:
		result = {}
		_, description = help.split(":", 1)
		description = description.strip()

		result['text'] = ""
		for line in description.split("\n"):
			# Remove any extra spaces or tabs from the beginning of the line
			result['text'] += line.strip() + "\n"
		# Remove the last newline character
		result['text'] = result['text'].strip()
		
		return result

	def parse_examples(self, help: str) -> dict:
		result = {}
		lines = [line.strip() for line in help.split("\n")]

		commands = []
		# The first line is the section name, so we skip it
		for line in lines[1:]:
			# Each example has format: command # description [ # context ]
			parts = line.split("#")
			if not parts[0]:
				continue
			if len(parts) > 2 and "needs buda" in parts[2].lower():
				# This example needs buda, so we skip it for now
				continue

			command_dict = {}
			# Get the command result
			command_dict['result'] = execute_debuda_command(parts[0].strip())

			# Use the description if provided, otherwise use "Command:"
			if len(parts) > 1:
				command_dict['text'] = parts[1].strip()
			else:
				command_dict['text'] = "Command:"
			
			# Command call
			command_dict['code'] = parts[0]

			commands.append(command_dict)
		
		result['commands'] = commands

		return result
	
	def parse_common_options(self, common_options: list) -> dict:
		# Common options are extracted from command metadata
		result = {}
		for option in common_options:
			if option not in OPTIONS:
				WARNING(f"Invalid option name: {option}. Skipping...")
				continue
			result[option] = OPTIONS[option]

		return result



class CmdPPrinter(SectionPPrinter):
	def __init__(self):
		""" The pretty printer class for debuda command documentation.
		"""
		super().__init__()
		self.section_printers = {
			"Usage": self.print_usage,
			"Description": self.print_description,
			"Arguments": self.print_arguments,
			"Options": self.print_arguments,
			"Examples": self.print_examples,
			"Common options": self.print_arguments
		}

	def print_docs(self, cmd_data: dict) -> str:
		result = ""
		for sec in self.section_printers.keys():
			if sec in cmd_data['docs']:
				result += self.eprinter.print_section(
					sec,
					self.section_printers[sec](cmd_data['docs'][sec])
				)
		
		return self.eprinter.print_section(cmd_data['title'], result, 2)



def get_module_metadata(module_path: os.PathLike) -> dict:
    """
    Fetch a module from a given filepath and get its docstring and metadata.
    
    Args:
    - module_path (os.PathLike): The file path to the module.
    
    Returns:
    - Docstring and metadata dictionary.
    """
    module_name = os.path.splitext(os.path.basename(module_path))[0]
    
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None:
        raise ImportError(f"Cannot find module at path: {module_path}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return module.command_metadata


def parse_source_file(input_file: os.PathLike, parser: CmdParser = CmdParser()) -> str:
	INFO(f"Parsing {input_file}...")
	result = {}

	cmd_metadata = get_module_metadata(input_file)
	cmd_doc = cmd_metadata["description"]

	if cmd_metadata["type"] == "dev":
		WARNING(f"Skipping {input_file} as it is a dev command")
		return None
	if "limited" not in cmd_metadata["context"]:
		WARNING(f"Skipping {input_file} as it is not a limited command (context: {cmd_metadata['context']})")
		return None
	
	# Add command name as title
	result['title'] = ""
	# Get the command name in long/short format, or long or short if only one is provided
	if cmd_metadata.get("long"):
		result['title'] += f"{cmd_metadata['long']}"
	if cmd_metadata.get("short"):
		if cmd_metadata.get("long"):
			result['title'] += " / "
		result['title'] += f"{cmd_metadata['short']}"

	result['docs'] = parser.parse(cmd_doc, cmd_metadata.get("common_option_names"))

	return result


def parse_directory(
	root: os.PathLike,
	parser: CmdParser = CmdParser(),
	interactive: bool = False
	) -> str:

	result = []
	for file in os.listdir(root):
		if file.endswith(".py") and not file.startswith("__"):

			if interactive:
				response = input(f"Process {file}? (Y/n): ")
				if response.lower() != "y" and response.lower() != "yes" and response.lower() != "":
					continue

			INFO(f"Processing {file}")
			process_result = parse_source_file(os.path.join(root, file), parser)
			if process_result:
				result.append(process_result)

		else:
			WARNING(f"Skipping: {file}. Not command file.")

	return result



if __name__=="__main__":
	args = docopt(__doc__)
	isfile = os.path.isfile(args["<input>"])
	isdir  = os.path.isdir(args["<input>"])

	if not isfile and not isdir:
		ERROR("Invalid input. Please provide a valid file or directory.")
		sys.exit(1)
	elif isfile:
		parser_result = [parse_source_file(args["<input>"])]
	elif isdir:
		parser_result = parse_directory(args["<input>"], interactive=args["--interactive"])

	output = ""
	cmd_printer = CmdPPrinter()
	for cmd in parser_result:
		output += cmd_printer.print_docs(cmd)
		output += "\n\n"

	if args["<output_file>"]:
		with open(args["<output_file>"], "a" if args["--append"] else "w") as f:
				f.write(output)
	else:
		print(output)
