# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import subprocess
from datetime import datetime

__requires__ = ["pip >= 24.0"]

from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext

# TTLens files to be copied to build directory
ttlens_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ttlens")
ttlens_home = os.path.dirname(ttlens_folder_path)


def get_ttlens_py_files(file_dir: os.PathLike = f"{ttlens_home}/ttlens", ignorelist: list = []) -> list:
    """A function to get the list of files in the ttlens lib directory.
    Ignore the files in the ignorelist."""

    files = os.listdir(file_dir)
    files = [f for f in files if f.endswith(".py")]
    files = [f for f in files if f not in ignorelist]

    return files


def get_libjtag() -> list:
    """A function to get the libjtag if it exists."""

    if os.path.exists(f"{ttlens_home}/build/lib/libjtag.so"):
        return ["libjtag.so", "libjlinkarm.so"]

    return []


ttlens_files = {
    "ttlens_lib": {"path": "ttlens", "files": get_ttlens_py_files(), "output": "ttlens"},
    "ttlens_fw": {
        "path": "ttlens/fw",
        "files": "*",  # Include all files in the ttlens/fw directory
        "output": "ttlens/fw",
    },
    "ttlens_commands": {
        "path": "ttlens/ttlens_commands",
        "files": get_ttlens_py_files(f"{ttlens_home}/ttlens/ttlens_commands"),
        "output": "ttlens/ttlens_commands",
    },
    "libs": {"path": "build/lib", "files": ["libdevice.so", "ttlens_pybind.so"], "output": "build/lib", "strip": True},
    "ttlens-server-standalone": {
        "path": "build/bin",
        "files": ["ttlens-server-standalone"],
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
        subprocess.check_call([f"cd {ttlens_home} && make"], env=env, shell=True)

    def _copy_files(self, target_path):
        strip_symbols = os.environ.get("STRIP_SYMBOLS", "0") == "1"
        for _, d in ttlens_files.items():
            path = target_path + "/" + d["output"]
            os.makedirs(path, exist_ok=True)

            src_path = ttlens_home + "/" + d["path"]
            if d["files"] == "*":
                self.copy_tree(src_path, path)
            else:
                for f in d["files"]:
                    self.copy_file(src_path + "/" + f, path + "/" + f)
                    if d.get("strip", False) and strip_symbols:
                        print(f"Stripping symbols from {path}/{f}")
                        subprocess.check_call(["strip", path + "/" + f])


# Fake TTLens extension
ttlens_fake_extension = TTExtension("ttlens.fake_extension")

with open("README.md", "r") as f:
    long_description = f.read()

# Add specific requirements for TTLens
with open(f"{ttlens_folder_path}/requirements.txt", "r") as f:
    requirements = [r for r in f.read().splitlines() if not r.startswith("-r")]

short_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("ascii").strip()
date = datetime.today().strftime("%y%m%d")

version = "0.1." + date + "+dev." + short_hash

setup(
    name="ttlens",
    version=version,
    packages=["ttlens"],
    package_dir={"ttlens": "ttlens"},
    author="Tenstorrent",
    url="http://www.tenstorrent.com",
    author_email="info@tenstorrent.com",
    description="Debugger for Tenstorrent devices",
    python_requires=">=3.8",
    ext_modules=[ttlens_fake_extension],
    cmdclass=dict(build_ext=MyBuild),
    zip_safe=False,
    install_requires=requirements,
    license="TBD",
    keywords="debugging tenstorrent",
    entry_points={"console_scripts": ["tt-lens = ttlens.cli:main"]},
)
