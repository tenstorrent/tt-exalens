"""
covdump.py

Given the currently running ELF, its .gcno, and the output directory, dump the coverage data
from the device into a .gcda file, and copy the .gcno there such that it has the same name.

Note that the ELF is needed for knowing the offset in L1 where coverage data resides.
As the L1 offset is the same for all ELFs for a given baby RISC core on a given architecture,
this script can be adjusted to take the arch and RISC type instead of the ELF, should that be necessary.
That is, however, less flexible, as this will work even through linker script changes.

Usage:
    python covdump.py kernel.elf coverage.gcda
"""

import argparse
import shutil
from pathlib import Path

from elftools.elf.elffile import ELFFile
from ttexalens.tt_exalens_init import init_ttexalens
from ttexalens.tt_exalens_lib import read_words_from_device, read_from_device

def get_symbol_address(elf_path: Path, symbol_name: str) -> int:
    """Return the address of an ELF symbol if it exists, otherwise exit."""
    with open(elf_path, 'rb') as f:
        elf = ELFFile(f)
        symtab = elf.get_section_by_name('.symtab')
        if not symtab:
            print(f"covdump: {f}: no .symtab")
            exit(1)

        for symbol in symtab.iter_symbols():
            if symbol.name == symbol_name:
                return symbol.entry['st_value']

    print(f"covdump: {f}: symbol {symbol_name} not found")
    exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Extract coverage data given the currently running ELF."
    )
    parser.add_argument("elf", help="Currently running ELF you wish to get the coverage data for.")
    parser.add_argument("gcno", help="Path to the corresponding .gcno file.")
    parser.add_argument("outdir", help="Directory to dump the coverage data and notes into.")
    args = parser.parse_args()

    elf_path = Path(args.elf).resolve()
    gcno_path = Path(args.gcno).resolve()
    outdir = Path(args.outdir).resolve()

    if not elf_path.exists():
        print(f"covdump: {elf_path}: file does not exist")
        exit(1)
    if not gcno_path.exists():
        print(f"covdump: {gcno_path}: file does not exist")    
        exit(1)

    length_addr = get_symbol_address(args.elf, "__coverage_start")
    data_addr = length_addr + 4

    context = init_ttexalens()
    core_loc = "0,0"

    length = read_words_from_device(
        core_loc,
        addr=length_addr,
        word_count=1,
        context=context
    )
    n = length[0]

    if n == 0xdeadbeef:
        print(f"covdump: {args.elf}: coverage region overflowed")
        exit(1)

    data = read_from_device(
        core_loc,
        data_addr,
        num_bytes=n,
        context=context
    )

    outdir.mkdir(parents=True, exist_ok=True)
    basename = elf_path.stem
    gcda_path = outdir / f"{basename}.gcda"
    gcno_copy_path = outdir / f"{basename}.gcno"

    try:
        shutil.copy2(gcno_path, gcno_copy_path)
    except Exception as e:
        print(f"covdump: while writing gcno: {e}")
        exit(1)

    try:
        with open(gcda_path, "wb") as f:
            f.write(data)
    except Exception as e:
        print(f"covdump: while writing gcda: {e}")
        exit(1)
    
    exit(0)

if __name__ == "__main__":
    main()
