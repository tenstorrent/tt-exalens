#!/usr/bin/env python3

"""
covdump.py

Given the currently running ELF and the output path, dump the coverage data from the device into the output file.
Note that the only thing the ELF is used for is getting the address at which coverage data begins.
This is uniform across all ELFs for a given baby RISC core (granted they're compiled with the same linker scripts),
but the most future-proof way to design this is to ask for the exact ELF and read its symbol table.

Usage:
    python covdump.py kernel.elf coverage.gcda
"""

import argparse
from elftools.elf.elffile import ELFFile
from ttexalens.tt_exalens_init import init_ttexalens
from ttexalens.tt_exalens_lib import read_words_from_device, read_from_device

def get_symbol_address(elf_path, symbol_name):
    """Return the address of an ELF symbol."""
    with open(elf_path, 'rb') as f:
        elf = ELFFile(f)
        symtab = elf.get_section_by_name('.symtab')
        if not symtab:
            print(f"covdump: {f}: no symbol table")
            return None

        for symbol in symtab.iter_symbols():
            if symbol.name == symbol_name:
                return symbol.entry['st_value']

    print(f"covdump: {f}: symbol {symbol_name} not found")
    return None

def main():
    parser = argparse.ArgumentParser(
        description="Read coverage data from the device, given the currently running ELF."
    )
    parser.add_argument("elf", help="Currently running ELF you wish to get the coverage data for.")
    parser.add_argument("outfile", help="File to dump the coverage data into.")
    args = parser.parse_args()

    length_addr = get_symbol_address(args.elf, "__coverage_start")
    if length_addr == None:
        exit(1)

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

    with open(args.outfile, "wb") as f:
        f.write(data)
    exit(0)

if __name__ == "__main__":
    main()
