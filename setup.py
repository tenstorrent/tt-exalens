# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import subprocess
from datetime import datetime

__requires__ = ['pip >= 24.0']

from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext

# Debuda files to be copied to build directory
dbd_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dbd')
debuda_home = os.path.dirname(dbd_folder_path)


def get_debuda_py_files(file_dir: os.PathLike = f"{debuda_home}/dbd", ignorelist: list = []) -> list:
    """A function to get the list of files in the debuda lib directory.
    Ignore the files in the ignorelist."""

    files = os.listdir(file_dir)
    files = [f for f in files if f.endswith(".py")]
    files = [f for f in files if f not in ignorelist]

    return files


debuda_files = {
    "debuda": {
        "path": "",
        "files": ["debuda.py"],
        "output": ""
    },
    "debuda_lib": {
        "path": "dbd",
        "files": get_debuda_py_files(),
        "output": "dbd"
    },
    "debuda_commands": {
        "path": "dbd/debuda_commands",
        "files": get_debuda_py_files(f"{debuda_home}/dbd/debuda_commands"),
        "output": "dbd/debuda_commands"
    },
    "libs": {
        "path": "build/lib",
        "files": [ "libdevice.so", "tt_dbd_pybind.so" ],
        "output": "build/lib",
        "strip": True
    },
    "debuda-server-standalone": {
        "path": "build/bin" ,
        "files": [ "debuda-server-standalone", "debuda-create-ethernet-map-wormhole", "debuda-create-ethernet-map-blackhole" ],
        "output": "build/bin",
        "strip": True
    }
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
        print(f"make -j{nproc} build")
        subprocess.check_call([f"cd {debuda_home} && make -j{nproc} build"], env=env, shell=True)

    def _copy_files(self, target_path):
        strip_symbols = os.environ.get("STRIP_SYMBOLS", "0") == "1"
        for _, d in debuda_files.items():
            path = target_path + "/" + d["output"]
            os.makedirs(path, exist_ok=True)

            src_path = debuda_home + "/" + d["path"]
            if d["files"] == "*":
                self.copy_tree(src_path, path)
            else:
                for f in d["files"]:
                    self.copy_file(src_path + "/" + f, path + "/" + f)
                    if d.get("strip", False) and strip_symbols:
                        print(f"Stripping symbols from {path}/{f}")
                        subprocess.check_call(["strip", path + "/" + f])

# Fake Debuda extension
debuda_fake_extension = TTExtension("debuda.fake_extension")

with open("README.md", "r") as f:
    long_description = f.read()

# Add specific requirements for Debuda
with open(f"{dbd_folder_path}/requirements.txt", "r") as f:
    requirements = [r for r in f.read().splitlines() if not r.startswith("-r")]

short_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
date = datetime.today().strftime('%y%m%d')

version = "0.1." + date + "+dev." + short_hash

setup(
    name='debuda',
    version=version,

    py_modules=['debuda'],
    package_dir={"debuda": "."},

    author='Tenstorrent',
    url="http://www.tenstorrent.com",
    author_email='info@tenstorrent.com',
    description='Debugger for Tenstorrent devices',
    python_requires='>=3.8',
    #long_description=long_description,
    #long_description_content_type="text/markdown",
    ext_modules=[debuda_fake_extension],
    cmdclass=dict(build_ext=MyBuild),
    zip_safe=False,
    install_requires=requirements,
    license="TBD",
    keywords="debugging tenstorrent",
    entry_points={
        'console_scripts': [
            'debuda = debuda:main'
        ]
    },
)
