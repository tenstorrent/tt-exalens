# AGENTS.md

Guidance for coding agents working in this repository. Setup instructions for people are in [README.md](README.md).

tt-exalens is a low-level debugger for Tenstorrent hardware: Wormhole, Blackhole and Quasar. It ships as the `ttexalens` Python library and the `tt-exalens` CLI. Both reach devices through tt-umd locally, or through a tt-exalens server remotely.

## Repository map

- `ttexalens/tt_exalens_lib.py`: public library functions, exported through `ttexalens/__init__.py`.
- `ttexalens/context.py`, `device.py`, `coordinate.py`: the core model. A `Context` holds `Device`s, and an `OnChipCoordinate` addresses a block on a device.
- `ttexalens/umd_device.py`: local device access through tt-umd (version pinned in `ttexalens/requirements.txt`). `ttexalens/server.py`: remote access.
- `ttexalens/hardware/`: blocks, memory maps, registers and RISC debug, with per-architecture code in `wormhole/`, `blackhole/` and `quasar/`.
- `ttexalens/cli.py`, `ttexalens/cli_commands/`: the CLI application, one module per command.
- `ttexalens/cpp/`: native ELF/DWARF code, built into `ttexalens._native_ttexalens` with nanobind. The Python side is `ttexalens/elf/`.
- `ttexalens/gdb/`: the GDB server.
- `riscv-src/`: RISC-V test kernels that the tests load onto cores.
- `test/ttexalens/unit_tests/`, `test/app/`, `test/wheel/`: library tests, CLI tests and installed-wheel tests.
- `docs/`: tutorials and generated references. The generators are in `docs/bin/`.

## Build and static checks

- `make` (same as `make build`) configures `build_debug/` and links it as `build/`. It builds the native module and the RISC-V test kernels, downloading the SFPI toolchain on the first run, then runs mypy and basedpyright. Rerun it after changing `ttexalens/cpp/` or `riscv-src/`.
- The build copies `_native_ttexalens*.so` into `ttexalens/` and generates its type stub `ttexalens/_native_ttexalens/__init__.pyi`. Both are gitignored. Importing `ttexalens` and type-checking both need them, so build first.
- `./scripts/install-deps.sh` installs the Python dependencies into the current environment. `./scripts/create-venv.sh` creates `.venv` instead.
- `pre-commit run --all-files` runs the same checks as CI: black (line length 120), ruff (unused imports), clang-format, the SPDX copyright check and whitespace fixers. New source files need the SPDX header; copy it from a neighboring file.
- `make mypy` and `make pyright` run the type checkers on their own. CI runs both.
- Code must run on Python 3.10 and newer.

## Running the CLI

- `./tt-exalens.py` runs the CLI from the working tree. For a non-interactive run, pass semicolon-separated commands and end with `x` (exit): `./tt-exalens.py --commands "brxy 0,0 0x0 4; x"`.
- A script run from outside the repository root imports an installed `tt-exalens` wheel if one exists, not the working tree. Set `PYTHONPATH` to the repository root.

## Tests

- Most tests need a Tenstorrent device. To use a simulator instead, set `TTEXALENS_SIMULATOR=<path>`. To use a running tt-exalens server, set `TTEXALENS_TESTS_REMOTE=1`. `TTEXALENS_TESTS_NOC_ID=0|1` selects the NOC.
- Run tests from the repository root after `make`, because they load kernels from `build/riscv-src/<arch>/`. Example: `python3 -m pytest test/ttexalens/unit_tests/test_lib.py -k write_read`.
- CI runs the suites with `python3 -m unittest discover`. Write tests as `unittest.TestCase` classes and parametrize them with `parameterized`. pytest-only features such as fixtures and marks don't run in CI.
- CI runs on a Blackhole p150b, a Wormhole n150 and a Wormhole n300, each with NOC0 and NOC1. If a test needs a device, core or block that some board lacks, call `self.skipTest(...)` rather than fail.

## Library API

- The public surface is `__all__` in `ttexalens/__init__.py`. To add a public function, put it in `tt_exalens_lib.py` with `@trace_api`, give it a typed signature and a docstring in the generator's format (see "Generated documentation"), and export it in `__init__.py`.
- Follow the existing signature shape: `location: str | OnChipCoordinate`, `device_id`, `context: Context | None`, then the optional `noc_id` and `safe_mode`. Resolve them with the helpers in `ttexalens/_lib_helpers.py`: `convert_coordinate`, `validate_addr` and `check_noc_id`.
- tt-metal's `tools/triage` imports much more than `__all__`, including `context`, `coordinate`, `device`, `umd_device`, `hardware.risc_debug`, `elf`, `memory_access` and `gdb`. Search tt-metal for usages before renaming anything or changing a signature in those modules.

## CLI commands

- The CLI loads every module in `ttexalens/cli_commands/` automatically. Each one must define `command_metadata = CommandMetadata(...)` and `run(cmd_text, context, ui_state)`. Short names must be unique.
- The module docstring is the docopt spec. It is also the `help` text and the source of the generated docs, so the parser's rules apply:
  - Separate sections with blank lines.
  - Separate each option from its description with at least two spaces.
  - Write examples as `command    # description`.
- Shared options such as `-d`, `-l` and `--neo` go in the usage line. Their descriptions come from `common_option_names`, so don't repeat them under `Options:`.
- `make docs` runs every example in the docstring on the attached device and puts its output in the docs, so examples must run as written.

## Generated documentation

- `make docs` generates `docs/ttexalens-lib-docs.md` and `docs/ttexalens-app-docs.md`. Don't edit them by hand. Regenerate them when you change the signature or docstring of a public function, or the docstring of a command.
- `make docs` builds, installs dependencies, then runs two generators:
  - `python3 -m docs.bin.generate-lib-docs ttexalens docs/ttexalens-lib-docs.md` parses the source and needs no device.
  - `python3 -m docs.bin.generate-command-docs ttexalens/cli_commands docs/ttexalens-app-docs.md` runs the examples. It needs a device, and the output it captures comes from that device.
- The committed app docs were generated on a Wormhole board. Several examples load Wormhole ELFs, and the `riscv` examples need brisc at 0,0 out of reset. On a Blackhole, or with that core in reset, those examples lose their output, so check the diff before committing regenerated app docs.
- The generators leave trailing whitespace, which CI's pre-commit check rejects. Run `pre-commit run --files docs/ttexalens-lib-docs.md docs/ttexalens-app-docs.md` before committing.
- The lib-docs generator parses every docstring in the modules that `ttexalens/__init__.py` imports, including docstrings of private methods, not only the exported items:
  - The first paragraph is the description.
  - Every later paragraph must start with a section header line: `Args:`, `Returns:` or `Notes:`. A paragraph without one is skipped with a warning and doesn't reach the docs.
  - Write arguments as `name (type): description`, and return values as `type: description`. A malformed `Args:`, `Returns:` or `Notes:` section can make generation fail.
- The other files in `docs/` (tutorials, `coordinates.md`, `exceptions.md`, `gdb.md` and the rest) are hand-written. Update them when the behavior they describe changes.

## Hardware safety

- A bad device access can hang or crash the device, not just fail. Safe mode checks every NOC access against the memory map of the block it targets. It is on by default. Turn it off with `--unsafe-mode` for the whole app, `--unsafe` for one command, or `safe_mode=False` in the library. If the check rejects a legitimate region, add the region to the architecture's memory map rather than turning safe mode off.
- NOC accesses outside L1 and DRAM use UMD's register API, 4 bytes at a time. The memory map decides this through `register_access`. Don't force bulk access on register space.
- Halting a RISC core, resetting it or putting it in debug mode changes its state. Leave cores in a known state, and prefer non-intrusive reads. Ethernet cores run base firmware, and halting them can wedge it.

## Design and review

`.github/skills/tt-exalens-review/SKILL.md` is the guide for reviewing pull requests, and its principles set the bar for new code too. The main ones:

- Keep architecture differences in the classes under `ttexalens/hardware/<arch>/`.
- Pass the codebase's own types, such as `OnChipCoordinate` and `NocId`, rather than raw values.
- Raise `TTException` subclasses for user errors (see `docs/exceptions.md`).
- Reuse existing helpers before adding new ones.
