# SPDX-FileCopyrightText: (c) 2026 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
"""Dynamic metadata provider to read dependencies from requirements.txt"""


def dynamic_metadata(fields, settings):
    """Read dependencies from ttexalens/requirements.txt"""
    from pathlib import Path

    req_file = Path(__file__).parent / "ttexalens" / "requirements.txt"
    dependencies = []

    for line in req_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            # Remove inline comments
            line = line.split("#")[0].strip()
            if line:
                dependencies.append(line)

    # Return just the list, not a dict
    return dependencies
