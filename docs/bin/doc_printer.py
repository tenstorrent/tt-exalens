# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from typing import List, Dict

class DocPrettyPrinter:
	def __init__(self, valid_sections: list = None, section_printers: dict = None):
		""" The pretty printer class for debuda command documentation. 
		
		Args:
		- valid_sections (list): List of valid section names to be printed.
		- section_printers (dict): Dictionary of section names and their corresponding printing functions.
		"""
		if valid_sections:
			self.valid_section_names = valid_sections
		else:
			self.valid_section_names = ["Usage", "Description", "Arguments", "Options", "Common options", "Examples"]

		if section_printers:
			self.section_printers = section_printers
		else:
			self.section_printers = {
				"Usage": self.print_usage,
				"Description": self.print_description,
				"Arguments": self.print_arguments,
				"Options": self.print_options,
				"Examples": self.print_examples,
				"Common options": self.print_options
			}


	def print_cmd(self, cmd_data: dict) -> str:
		result = ""
		
		result += self._print_title(cmd_data['title'])

		for sec in self.valid_section_names:
			if sec in cmd_data['docs']:
				result += self._print_section_title(sec)
				result += self.section_printers[sec](cmd_data['docs'][sec])
				result += "\n\n"
		
		return result

	# Functions to print by section

	def print_usage(self, usage: str) -> str:
		return self._print_code(usage['code'])
	
	def print_description(self, description: dict) -> str:
		return self._print_text(description['text'])
	
	def print_arguments(self, arguments: dict) -> str:
		return self._print_itemized(arguments)
	
	def print_options(self, options: dict) -> str:
		result = ""
		for cl, desc in options.items():
			result += f"- **{cl}"											 # Option name
			result += f", {desc['short']}" if 'short' in desc.keys() else "" # Option short name
			if 'arg' in desc.keys():
				argstring = desc['arg']
				result += f" {argstring}"									# Option argument
			result += f"** : {desc['description']}\n"						# Option description
		return result
	
	def print_examples(self, examples: list) -> str:
		return self._print_commands(examples['commands'])


	# Functions to print by format

	def _print_code(self, code: str) -> str:
		return f"```\n{code}\n```\n"
	
	def _print_itemized(self, itemized: dict) -> str:
		# itemized is a dictionary of arguments and their descriptions
		result = ""
		for arg, desc in itemized.items():
			result += f"- **{arg}**:  {desc}\n"
		return result
	
	def _print_commands(self, commands: list) -> str:
		result = ""
		for cmd in commands:
			result += f"{cmd['text']}\n"					# Command description
			result += self._print_code(cmd['code'])			# Command call
			if cmd['result']:								# Command result
				result += "Output:\n"						
				result += self._print_code(cmd['result'])
			result += "\n"
		return result

	def _print_title(self, title: str) -> str:
		return f"## {title}\n\n\n"
	
	def _print_section_title(self, section: str) -> str:
		return f"### {section}\n\n"

	def _print_text(self, text: str) -> str:
		return text + "\n"



class ElementPPrinter:
	def __init__(self):
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
	
	def print_arg(self, 
			   argname: str = None, 
			   argdesc: str = None, 
			   argtype: str = None, 
			   optarg: str = None,
			   optshort:str = None
		) -> str:
		result = f"`{argname}" if argname else ""
		
		result += f", {optshort}`" if optshort else ""
		result += "`" if optshort or argname else ""
		result += f" = **{optarg}**" if optarg else ""
		
		if type(argtype) == list:
			argtype = ", ".join(argtype)
		result += f" *({argtype})*" if argtype else ""
		result += f": {argdesc}" if argdesc else ""

		return result



class SectionPPrinter:
	def __init__(self, element_printer: ElementPPrinter = ElementPPrinter()):
		self.eprinter = element_printer

	@abstractmethod
	def print_docs(self, docstring: Dict) -> str:
		pass

	def print_usage(self, usage: Dict) -> str:
		return self.eprinter.print_code(usage['code'])
	
	def print_description(self, description: dict) -> str:
		return self.eprinter.print_text(description['text'])
	
	def print_arguments(self, arguments: dict) -> str:
		argstrings = []
		for arg, desc in arguments.items():
			argname = arg
			argdesc = desc.get('description', None)
			argtype = desc.get('type', None)
			
			optarg = desc.get('arg', None)
			optshort = desc.get('short', None)

			argstrings.append(self.eprinter.print_arg(argname, argdesc, argtype, optarg, optshort))
		
		return self.eprinter.print_items(argstrings)
	
	def print_examples(self, examples: Dict) -> str:
		result = ""
		for cmd in examples['commands']: 
			result += self.eprinter.print_text(cmd['text']) 	# Command description
			result += self.eprinter.print_code(cmd['code'])		# Command call
			if cmd['result']:									# Command result
				result += self.eprinter.print_text("Output:")						
				result += self.eprinter.print_code(cmd['result'])

		return result

	def print_returns(self, returns: dict) -> str:
		return self.eprinter.print_arg(argtype=returns['type'], argdesc=returns['description'])
	
	def print_notes(self, notes: dict) -> str:
		return self.eprinter.print_items(notes['items'])


	