# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import subprocess
from datetime import datetime

__requires__ = ["pip >= 24.0"]

from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext

# TTExaLens files to be copied to build directory
ttexalens_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ttexalens")
ttexalens_home = os.path.dirname(ttexalens_folder_path)


def get_ttexalens_py_files(file_dir: os.PathLike = f"{ttexalens_home}/ttexalens", ignorelist: list = []) -> list:
    """A function to get the list of files in the ttexalens lib directory.
    Ignore the files in the ignorelist."""

    files = os.listdir(file_dir)
    files = [f for f in files if f.endswith(".py")]
    files = [f for f in files if f not in ignorelist]

    return files


def get_libjtag() -> list:
    """A function to get the libjtag if it exists."""

    if os.path.exists(f"{ttexalens_home}/build/lib/libttexalens_jtag.so"):
        return ["libttexalens_jtag.so", "libjlinkarm.so"]

    return []


ttexalens_files = {
    "ttexalens_lib": {"path": "ttexalens", "files": get_ttexalens_py_files(), "output": "ttexalens"},
    "cli_commands": {
        "path": "ttexalens/cli_commands",
        "files": get_ttexalens_py_files(f"{ttexalens_home}/ttexalens/cli_commands"),
        "output": "ttexalens/cli_commands",
    },
    "libs": {
        "path": "build/lib",
        "files": ["libdevice.so", "ttexalens_pybind.so"] + get_libjtag(),
        "output": "build/lib",
        "strip": True,
    },
    "ttexalens-server-standalone": {
        "path": "build/bin",
        "files": ["ttexalens-server-standalone"],
        "output": "build/bin",
        "strip": True,
    },
}


class TTExtension(Extension):
    def __init__(self, name):
        Extension.__init__(self, name, sources=[])


class MyBuild(build_ext):
    def run(self):
        build_lib = self.build_lib
        if not os.path.exists(build_lib):
            print("Creating build directory", build_lib)
            os.makedirs(build_lib, exist_ok=True)

        self._call_build()

        # Copy the files to the build directory
        self._copy_files(build_lib)

    def _call_build(self):
        env = os.environ.copy()
        nproc = os.cpu_count()
        print(f"make")
        subprocess.check_call([f"cd {ttexalens_home} && make"], env=env, shell=True)

    def _copy_files(self, target_path):
        strip_symbols = os.environ.get("STRIP_SYMBOLS", "0") == "1"
        for _, d in ttexalens_files.items():
            path = target_path + "/" + d["output"]
            os.makedirs(path, exist_ok=True)

            src_path = ttexalens_home + "/" + d["path"]
            if d["files"] == "*":
                self.copy_tree(src_path, path)
            else:
                for f in d["files"]:
                    self.copy_file(src_path + "/" + f, path + "/" + f)
                    if d.get("strip", False) and strip_symbols:
                        print(f"Stripping symbols from {path}/{f}")
                        subprocess.check_call(["strip", path + "/" + f])


# Fake TTExaLens extension
ttexalens_fake_extension = TTExtension("ttexalens.fake_extension")

with open("README.md", "r") as f:
    long_description = f.read()

# Add specific requirements for TTExaLens
with open(f"{ttexalens_folder_path}/requirements.txt", "r") as f:
    requirements = [r for r in f.read().splitlines() if not r.startswith("-r")]

short_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("ascii").strip()
date = datetime.today().strftime("%y%m%d")

version = "0.1." + date + "+dev." + short_hash

setup(
    name="ttexalens",
    version=version,
    packages=["ttexalens"],
    package_dir={"ttexalens": "ttexalens"},
    author="Tenstorrent",
    url="http://www.tenstorrent.com",
    author_email="info@tenstorrent.com",
    description="Debugger for Tenstorrent devices",
    python_requires=">=3.8",
    ext_modules=[ttexalens_fake_extension],
    cmdclass=dict(build_ext=MyBuild),
    zip_safe=False,
    install_requires=requirements,
    license="TBD",
    keywords="debugging tenstorrent",
    entry_points={"console_scripts": ["tt-lens = ttexalens.cli:main"]},
)
