#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  generate-command-docs.py <input> <output_file> [-a]
  generate-command-docs.py <input> [-i]

Arguments:
  <input>  			 Directory containing command files to parse, or a single command file to parse.
  <output_file>      Output .md file to write to. If not provided, the output will be printed to stdout.

Options:
  -a, --append       Append to the output file instead of overwriting it.
  -i, --interactive  Run in interactive mode. Pause after parsing each file.

Description:
  This is a script for automatically generating markdown documentation for debuda commands
  using their docop strings. The script can be run on a single command file or a directory.
  If examples are provided, the script will try to run them and include the output in the
  documentation if no error occurs. 
"""
import sys, re, os
from docopt import docopt

# We limit what each example can output to avoid spamming the user
MAX_OUTPUT_LINES = 20  # Max number of lines to show for each example
MAX_CHARACTERS_PER_LINE = 130  # Max number of characters to show for each line

from run_debuda_on_help_examples import execute_debuda_command

def INFO(text:str) -> None:
    print(f"\033[1;32m{text}\033[0m")

def WARNING(text:str) -> None:
    print(f"\033[1;33m{text}\033[0m")

def ERROR(text:str) -> None:
    print(f"\033[1;31m{text}\033[0m")


valid_section_names = ["Usage", "Arguments", "Options", "Description", "Examples"]

def parse_usage(help: str) -> str:
	result = ""
	lines = [line.strip() for line in help.split("\n")]

	result += "### " + lines[0][:-1] + "\n\n"
	result += "```\n" + lines[1] + "\n```" + "\n"
	result += "\n\n\n"
	
	return result

def parse_arguments(help: str) -> str:
	result = ""
	lines = [line.strip() for line in help.split("\n")]

	result += "### " + lines[0][:-1] + "\n\n"
	for line in lines[1:]:
		line = re.split(r'\s{2,}', line)
		if len(line) > 1:
			result += "\n\n- **" + line[0] + "**:  " + line[1]
		else:
			result += " " + line[0]
	result += "\n\n"

	return result

def parse_options(help: str) -> str:
	result = parse_arguments(help)
	return result

def parse_description(help: str) -> str:
	result = ""
	title, description = help.split(":", 1)
	description = description.strip()

	result += "### " + title + "\n\n"
	for line in description.split("\n"):
		result += line.strip() + "\n"
	
	result += "\n\n"
	
	return result

def parse_examples(help: str) -> str:
	result = ""
	lines = [line.strip() for line in help.split("\n")]

	result += "### " + lines[0][:-1] + "\n\n"

	for line in lines[1:]:
		parts = line.split("#")
		if not parts[0]:
			continue
		if len(parts) > 2 and "needs buda" in parts[2].lower():
			continue

		command_result = execute_debuda_command(parts[0].strip())

		if len(parts) > 1:
			result += parts[1].strip() + ":\n\n"
		else:
			result += "Command:\n\n"
		
		result += "```\n" + parts[0] + "\n```\n\n"

		if command_result!="":
			result += "Output:\n\n"
			result += "```\n" + command_result + "\n```\n\n"

	return result

section_parsers = {
	"Usage": parse_usage,
	"Arguments": parse_arguments,
	"Options": parse_options,
	"Description": parse_description,
	"Examples": parse_examples
}


def extract_metadata(metadata: str):
	short = None
	long = None
	cmd_type = None
	started = False
	
	for line in metadata.split("\n"):
		# Find command_metadata
		if not started and line.strip().startswith("command_metadata"):
			started = True
		elif not started:
			continue

		# Find short and long names
		if line.strip().startswith('"short"'):
			short = line.split(":")[1].strip().replace('"', "").replace(",", "")
		elif line.strip().startswith('"long"'):
			long = line.split(":")[1].strip().replace('"', "").replace(",", "")
		elif line.strip().startswith('"context"'):
			context = line.split(":")[1].strip().replace("[", "").replace("]", "").split(",")
			context = [c.strip().replace('"', "") for c in context if c!=""]
		elif line.strip().startswith('"type"'):
			cmd_type = line.split(":")[1].strip().replace('"', "").replace(",", "")
		elif "}" in line.strip():
			break
	
	callstring = ""
	if long:
		callstring += long
	if long and short:
		callstring += " / "
	if short:
		callstring += short

	return callstring, context, cmd_type

def parse_source_file(input_file: os.PathLike, dry_run: bool = False) -> str:
	output_string = ""

	with open(input_file, "r") as f:
		doc = f.read()
		doc = doc.split('"""')
		
		if len(doc) < 3:
			ERROR(f"Skipping {input_file} as it does not have the required documentation")
			return ""

		callstring, context, cmd_type = extract_metadata(doc[2])
		if cmd_type == "dev":
			WARNING(f"Skipping {input_file} as it is a dev command")
			return ""
		elif "limited" not in context:
			WARNING(f"Skipping {input_file} as it is not a limited command (context: {context})")
			return ""

		output_string += f"## {callstring}\n\n"

		cmd_help = doc[1].strip()		
		sections = [sec.strip() for sec in cmd_help.split("\n\n")]
		for sec in sections:
			secname = sec.split("\n")[0].strip()[:-1]
			#                                   remove : at the end

			if secname not in valid_section_names:
				WARNING(f"Invalid section name: {secname} in file {input_file}. Skipping...")
				continue
			
			output_string += section_parsers[secname](sec)
		
	if dry_run:
		print(output_string)
		return ""
	
	return output_string


def parse_directory(
		directory: os.PathLike, 
		dry_run: bool = False, 
		interactive: bool = False
		) -> str:
	
	output_string = ""
	for root, _, files in os.walk(directory):
		for file in files:
			if file.endswith(".py") and not file.startswith("__"):
				INFO(f"Processing {file}")
				output_string += parse_source_file(os.path.join(root, file), dry_run)
			else:
				WARNING(f"Skipping: {file}. Not command file.")
			
			if interactive:
				input("Press Enter to continue...")
	return output_string

if __name__=="__main__":
	args = docopt(__doc__)
	isfile = os.path.isfile(args["<input>"])
	isdir  = os.path.isdir(args["<input>"])

	if not isfile and not isdir:
		ERROR("Invalid input. Please provide a valid file or directory.")
		sys.exit(1)

	if args["<output_file>"]:
		if isfile:
			with open(args["<output_file>"], "w" if not args["--append"] else "a") as f:
				f.write(parse_source_file(args["<input>"]))
		elif isdir:
			with open(args["<output_file>"], "w" if not args["--append"] else "a") as f:
				f.write(parse_directory(args["<input>"]))

	else:
		if isfile:
			parse_source_file(args["<input>"], dry_run=True)
		elif isdir:
			parse_directory(args["<input>"], dry_run=True)
