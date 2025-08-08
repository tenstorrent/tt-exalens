"""
covdump.py

Given the currently running ELF and the output directory, dump the coverage data from the device into a .gcda file.
Also attempt to find its corresponding .gcno file from the debug symbols and put it in the same directory.

Note that the ELF is needed for knowing the offset in L1 where coverage data resides, and for finding its .gcno.
As the L1 offset is the same for all ELFs for a given baby RISC core, 
this script can be adjusted to take the RISC type and .gcno path instead, should that be necessary.

Usage:
    python covdump.py kernel.elf coverage.gcda
"""

import argparse
import shutil
import sys
from pathlib import Path

from elftools.elf.elffile import ELFFile
from ttexalens.tt_exalens_init import init_ttexalens
from ttexalens.tt_exalens_lib import read_words_from_device, read_from_device

def get_symbol_address(elf_path: Path, symbol_name: str) -> int | None:
    """Return the address of an ELF symbol if it exists, otherwise None."""
    with open(elf_path, 'rb') as f:
        elf = ELFFile(f)
        symtab = elf.get_section_by_name('.symtab')
        if not symtab:
            print(f"covdump: {f}: no .symtab")
            return None

        for symbol in symtab.iter_symbols():
            if symbol.name == symbol_name:
                return symbol.entry['st_value']

    print(f"covdump: {f}: symbol {symbol_name} not found")
    return None

def infer_paths(elf_path: Path) -> list[Path]:
    """Parse DWARF debug info and return possible .gcno paths."""
    paths: list[Path] = []
    with open(elf_path, "rb") as f:
        elf = ELFFile(f)
        if not elf.has_dwarf_info():
            print(f"covdump: {elf_path}: no debug info")
            exit(1)
        
        dwarf = elf.get_dwarf_info()
        for cu in dwarf.iter_CUs():
            top = cu.get_top_DIE()

            # The .gcno file is stored in the same directory as the object file.
            name_attr = top.attributes.get("DW_AT_name")
            comp_dir_attr = top.attributes.get("DW_AT_comp_dir")
            if not name_attr:
                continue
            
            src_name = _attr_to_str(name_attr)
            comp_dir = _attr_to_str(comp_dir_attr) if comp_dir_attr else ""
            
            src_path = Path(src_name)
            if src_path.is_absolute():
                possible = src_path.with_suffix(".gcno")
            else:
                possible = (Path(comp_dir) / src_path).with_suffix(".gcno") if comp_dir else src_path.with_suffix(".gcno")
            
            # Normalize.
            possible = Path(possible)
            s = str(possible)
            if s not in {str(p) for p in paths}:
                paths.append(possible)

    return paths

def get_gcno(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.is_file():
            return p
    return None

def _attr_to_str(attr):
    if attr is None:
        return ""
    v = attr.value
    if isinstance(v, (bytes, bytearray)):
        try:
            return v.decode("utf-8", "replace")
        except Exception:
            return v.decode("latin-1", "replace")
    return str(v)

def main():
    parser = argparse.ArgumentParser(
        description="Extract coverage data given the currently running ELF."
    )
    parser.add_argument("elf", help="Currently running ELF you wish to get the coverage data for.")
    parser.add_argument("outdir", help="Directory to dump the coverage data and notes into.")
    args = parser.parse_args()

    elf_path = Path(args.elf).resolve()
    outdir = Path(args.outdir).resolve()

    if not elf_path.exists():
        print(f"covdump: {elf_path}: file does not exist")
        exit(1)
    
    paths = infer_paths(elf_path)
    gcno = get_gcno(paths)
    if gcno is None:
        print(f"covdump: {elf_path}: could not find .gcno")
        exit(1)

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

    outdir.mkdir(parents=True, exist_ok=True)
    basename = Path(gcno.name).stem
    gcda = outdir / f"{basename}.gcda"
    gcno_copy = outdir / f"{basename}.gcno"

    try:
        shutil.copy2(gcno, gcno_copy)
    except Exception as e:
        print(f"covdump: while writing gcno: {e}")
        exit(1)

    try:
        with open(gcda, "wb") as f:
            f.write(data)
    except Exception as e:
        print(f"covdump: while writing gcda: {e}")
        exit(1)
    
    exit(0)

if __name__ == "__main__":
    main()
