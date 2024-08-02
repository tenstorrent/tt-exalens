#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import subprocess, re, os

# We limit what each example can output to avoid spamming the user
MAX_OUTPUT_LINES = 20  # Max number of lines to show for each example
MAX_CHARACTERS_PER_LINE = 130  # Max number of characters to show for each line


def run_command(cmd_array, exit_on_failure=True):
    if os.environ.get("COV", "0") == "1":
        cmd_array = ["coverage", "run", "--append", "--include=dbd/**"] + cmd_array

    process = subprocess.Popen(
        cmd_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # Capture all output
    stdout_output, stderr_output = process.communicate()

    # Convert output to lists of lines
    stdout_lines = stdout_output.strip().split("\n")
    stderr_lines = stderr_output.strip().split("\n")

    return_code = process.returncode
    if return_code != 0 and exit_on_failure:
        exit(1)

    return {
        "stdout": "\n".join(stdout_lines),
        "stderr": "\n".join(stderr_lines),
        "returncode": return_code,
    }


def strip_ansi(line):
    return re.sub(r"\x1b\[([0-9;:]+)?m", "", line)


def trim_line_and_append_elipsis(line, max_length):
    if len(line) > max_length:
        line = line[:max_length] + "..."
    return line


# Captures everything between the command and the exit command
def execute_debuda_command(command):
    full_command = ["./debuda.py", "--commands", f"{command}; x"]

    # Sometimes a sequence of commands is needed to get the correct output.
    # If that is the case, we only want to show the last command.
    interesting_command = command.split(";")[-1].strip()

    result = run_command(full_command, exit_on_failure=False)
    output_lines = result["stdout"].split("\n")

    filtered_output = []
    capture = False

    for line in output_lines:
        try:
            line = strip_ansi(line)
            skip_line = False
            if "Executing command: x" in line:
                capture = False
            if "Loading yaml file" in line:
                skip_line = True
            if "Warning: " in line:
                skip_line = True
            if capture and not skip_line:
                filtered_output.append(
                    trim_line_and_append_elipsis(line, MAX_CHARACTERS_PER_LINE)
                )
            if f"Executing command: {interesting_command}" in line:
                capture = True
        except Exception as e:
            print(f"Error parsing line: {line}")
            raise e

    if result["returncode"] != 0:
        return ""
    else:
        if len(filtered_output) > MAX_OUTPUT_LINES:
            filtered_output = filtered_output[:MAX_OUTPUT_LINES] + ["..."]
        filtered_output = "\n".join(filtered_output)

    return filtered_output


