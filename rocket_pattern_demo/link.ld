// SPDX-FileCopyrightText: (c) 2026 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
/* SPDX-License-Identifier: Apache-2.0 */
/* Bare-metal linker script for a Quasar Rocket core: everything lives in TL1,
 * origin 0x0 (the reset vector / code start address), 4 MB long. crt0's
 * .text.init is placed first so _start sits at 0x0. */
OUTPUT_ARCH(riscv)
ENTRY(_start)

MEMORY
{
    TL1 (rwx) : ORIGIN = 0x0, LENGTH = 4M
}

SECTIONS
{
    . = 0x0;

    .text.init : { KEEP(*(.text.init)) } > TL1
    .text      : { *(.text .text.*) }    > TL1

    .rodata    : { *(.rodata .rodata.* .srodata .srodata.*) } > TL1

    . = ALIGN(8);
    .data      : { *(.data .data.* .sdata .sdata.*) } > TL1

    . = ALIGN(8);
    .bss (NOLOAD) : {
        __bss_start = .;
        *(.bss .bss.* .sbss .sbss.* COMMON)
        . = ALIGN(8);
        __bss_end = .;
    } > TL1

    /DISCARD/ : {
        *(.comment)
        *(.note .note.*)
        *(.eh_frame .eh_frame_hdr)
        *(.riscv.attributes)
    }
}
