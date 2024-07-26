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
