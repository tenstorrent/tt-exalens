# ELF loader

## Goal and problems
Goal of the ELF loader is to load provided ELF file to specified RISC-V core.

Main problem that loader needs to solve is initialization of private memory that cannot be accessed from NOC.
There are two private memory blocks:
- 0xFFB00000 - block reserved for global variables and stack
- 0xFFC00000 - IRAM, block reserved for code on NCRISC on some architectures (grayskull and wormhole)

## Copying private memory
There are two approches that can be done:
1. Using debugging interface: to start application paused, load private memory and then continue execution
2. Double memory copy: copy private memory somewhere in L1 and program will copy memory to private memory before it starts main

### Approach 1: using debugging interface
We experimented with this approach, but hit many problems along the way:
- BNE instruction doesn't work when debug is enabled
- Clearing instruction cache is not reliable on grayskull/wormhole and it doesn't work on blackhole
- NCRISC doesn't have debug interface, so we cannot make loader this way for it

### Approach 2: double memory copy
This is known approach used in tt-metal. Here we have implemented a bit different version as application
writer doen't need to be aware of this in `.cc` file. Everything is done in loader and CRT.

## Final solution

We have two sections in elf that are just reserving memory (similar to `.stack` section):
- `.loader_init` - it is used for transfering data into `.ldm_data` section
- `.loader_code` - it is used for transfering code into `.init` section

These sections are defined in `section.ld` file. Values used there are being defined in `brisc.ld`/`triscX.ld`/`ncrisc.ld` file,
that are using memory blocks defined in `memory.*arch*.ld` files.

### .loader_init
CRT expects loader to copy `.ldm_data` section into `.loader_init` section space. When program starts, CRT will copy `.loader_init`
section data into `.ldm_data` section using simple loop and `LW` and `SW` instructions. This is done before global initialization,
since `__init_array_start` and `__init_array_end` point into `.ldm_data` section.

### .loader_code
This section is mostly empty and it is not being used if core doesn't have IRAM. Loader will copy data that will go to IRAM into
`.loader_code` section space. Also, since `.init` section points to IRAM, loader will make core start from `.loader_code` address (which is in L1).
CRT will copy whole `.loader_code` section into IRAM and do PC register manipulation to go back to IRAM to continue execution.
Since NCRISC core cannot write to IRAM, we need to use tensix DMA xmov.

This is how flow looks like:
- Compiler writes code in IRAM (0xffc00000) and it expects it to run there
- Loader cannot load memory into IRAM and expects CRT to do it
- Loader copies code that should go to IRAM to L1 (location defined by `.loader_code` section) and sets NCRISC start address to L1 address instead of IRAM
- CRT starts execution in L1, loads code to IRAM, then jumps to IRAM to continue execution
    - CRT cannot use LA instruction because it will be converted to AUIPC+ADDI and compiler expects PC to be in IRAM, so we need to manually use LUI+ADDI to load addresses
    - First CRT checks if `.loader_code` section is empty in order to skip loading IRAM and PC manipulation
    - It triggers tensix DMA xmov on mover 0
    - It waits until mover completes
    - CRT does address manipulation and jumps to IRAM on the same instruction to continue execution
