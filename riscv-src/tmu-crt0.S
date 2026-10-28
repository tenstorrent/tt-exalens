// SPDX-FileCopyrightText: (c) 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

// Pointer-sized loads and stores (init_array entries, argv slots) depend on XLEN; everything else
// works on 32-bit words, so the same code serves 32-bit and 64-bit cores.
#if __riscv_xlen == 64
#define REG_L ld
#define REG_S sd
#define SZREG 8
#else
#define REG_L lw
#define REG_S sw
#define SZREG 4
#endif

// sections.ld aligns the pointer arrays (init_array, ...) to this.
.global __crt0_pointer_size
.set    __crt0_pointer_size, SZREG

.section .init
.global _start
.type   _start, @function

_start:

CRT_START:
  # Since NCRISC has to load itself into address space that our loader cannot do, we need to do following magic:
  # - First we load bits on specific location in loader (to .loader_code section)
  # - Then we copy code from .loader_code to .init section
  # - Then we jump to .init section
  # - We do all of that with absolute addresses, since we are working in .loader_code section and we want to continue to .init section

  # Check if we need to copy .loader_code to .init (.loader_code section is empty on all cores except on NCRISC since that one has dedicated memory for instructions)
  la      t0, __loader_code_start      # Load the address of __loader_code_start into t0
  la      t1, __loader_code_end        # Load the address of __loader_code_end into t1
  beq     t0, t1, 3f                   # If t0 == t1, skip loading to IRAM since we don't have it

  # Copy memory from .loader_code to .init (we cannot use direct memory copy since NCRISC cannot write to IRAM, but tensix DMA xmov can)
  # Trigger tensix DMA xmov
  # We are using hardcoded values that work on every core with IRAM

  # *RISCV_TDMA_REG_XMOV_SRC_ADDR = source_address; // RISCV_TDMA_REG_XMOV_SRC_ADDR = 0xFFB11000; source_address = __loader_code_start << 4;
  li      t0, 0xFFB11000               # Load RISCV_TDMA_REG_XMOV_SRC_ADDR to t0
  # la    t1, __loader_code_start      # Load the address of __loader_code_start into t1
  lui     t1, %hi(__loader_code_start) # Load upper 20 bits of the address __loader_code_start into t1
  addi    t1, t1, %lo(__loader_code_start) # Add lower 12 bits of the address __loader_code_start to t1
  srli    t1, t1, 4                    # Logical shift right by 4 bits (fills with zeros)
  sw      t1, 0(t0)                    # Store the value from t1 into the memory location at t0

  # *RISCV_TDMA_REG_XMOV_DST_ADDR = destination_address; // RISCV_TDMA_REG_XMOV_DST_ADDR = 0xFFB11004; destination_address = 0x4000;
  li      t0, 0xFFB11004               # Load RISCV_TDMA_REG_XMOV_DST_ADDR to t0
  li      t1, 0x4000                   # Load MEM_MOVER_VIEW_IRAM_BASE_ADDR to t1
  sw      t1, 0(t0)                    # Store the value from t1 into the memory location at t0

  # *RISCV_TDMA_REG_XMOV_SIZE = lenght(.loader_code) >> 4; // RISCV_TDMA_REG_XMOV_SIZE = 0xFFB11008
  # li    t0, 0xFFB11008               # Load RISCV_TDMA_REG_XMOV_SIZE to t0
  lui     t0, 0xFFB11                  # Load upper 20 bits of RISCV_TDMA_REG_XMOV_SIZE to t0
  addi    t0, t0, 0x008                # Load lower 12 bits of RISCV_TDMA_REG_XMOV_SIZE to t0
  # la    t1, __loader_code_start      # Load the address of __loader_code_start into t1
  lui     t1, %hi(__loader_code_start) # Load upper 20 bits of the address __loader_code_start into t1
  addi    t1, t1, %lo(__loader_code_start) # Add lower 12 bits of the address __loader_code_start to t1
  # la    t2, __loader_code_end        # Load the address of __loader_code_end into t2
  lui     t2, %hi(__loader_code_end)   # Load upper 20 bits of the address __loader_code_end into t2
  addi    t2, t2, %lo(__loader_code_end) # Add lower 12 bits of the address __loader_code_end to t2
  sub     t1, t2, t1                   # t1 = t2 - t1
  srli    t1, t1, 4                    # Logical shift right by 4 bits (fills with zeros)
  sw      t1, 0(t0)                    # Store the value from t1 into the memory location at t0

  # *RISCV_TDMA_REG_XMOV_DIRECTION = XMOV_L1_TO_L0; // RISCV_TDMA_REG_XMOV_DIRECTION = 0xFFB1100C; XMOV_L1_TO_L0 = 1;
  li      t0, 0xFFB1100C               # Load RISCV_TDMA_REG_XMOV_DIRECTION to t0
  li      t1, 1                        # Load XMOV_L1_TO_L0 to t1
  sw      t1, 0(t0)                    # Store the value from t1 into the memory location at t0

  # *RISCV_TDMA_REG_COMMAND_ADDR = CMD_TDMA_XMOV | (TDMA_MOVER0 << 8); // RISCV_TDMA_REG_COMMAND_ADDR = 0xFFB11010; CMD_TDMA_XMOV = 0x40; TDMA_MOVER0 = 0;
  li      t0, 0xFFB11010               # Load RISCV_TDMA_REG_COMMAND_ADDR to t0
  li      t1, 0x40                     # Load CMD_TDMA_XMOV | (TDMA_MOVER0 << 8) to t1
  sw      t1, 0(t0)                    # Store the value from t1 into the memory location at t0

  # Wait until tensix DMA xmov finishes
  li t0, 0xFFB11014                    # Load address 0xFFB11014 into t0 (RISCV_TDMA_REG_STATUS)
  li t1, 0x08                          # Load RISCV_TDMA_STATUS_FLAG_FIFO_EMPTY_MASK into t1 (0x08)
  li t2, 0x01                          # Load RISCV_TDMA_STATUS_FLAG_MOVER0_BUSY_MASK into t2 (0x01)

  # Dummy read to flush the pipe
  lw t3, 0(t0)                         # Load the value from memory at 0xFFB11014 into t3

1:
  lw t3, 0(t0)                         # Load the value from memory at 0xFFB11014 into t3 (tdma_mover_status)
  or t4, t1, t2                        # t4 = RISCV_TDMA_STATUS_FLAG_MOVER0_BUSY_MASK | RISCV_TDMA_STATUS_FLAG_FIFO_EMPTY_MASK
  and t5, t3, t4                       # t5 = tdma_mover_status & t4
  bne t5, t1, 1b                       # If t5 != RISCV_TDMA_STATUS_FLAG_FIFO_EMPTY_MASK, loop

2:
  # We need to fix current PC. We will store PC into t0, then we will store __loader_code_start into t1 and __firmware_start into t2.
  # We calculate offset and use JALR to jump to .init section from here.
  jal     t0, address_fix              # Store PC + 4 into t0, since address_fix is just next instruction
address_fix:
  # la    t1, __loader_code_start
  lui     t1, %hi(__loader_code_start) # Store upper 20 bits of the address __loader_code_start into register t1
  addi    t1, t1, %lo(__loader_code_start) # Add lower 12 bits of the address __loader_code_start to t1
  # la    t2, __firmware_start
  lui     t2, %hi(__firmware_start)    # Store upper 20 bits of the address __loader_code_start into register t2
  addi    t2, t2, %lo(__firmware_start) # Add lower 12 bits of the address __firmware_start to t2
  sub     t2, t2, t1                   # t2 = t2 - t1
  add     t2, t2, t0                   # t2 = t2 + t0
  addi    t2, t2, 32                   # Offset t2 address for 8 instructions (32 bytes). It should point to label 3 in correct address space.
  jalr    x0, 0(t2)                    # Jump to address in register t2

3:
  # Initialize global pointer
  .option push
  .option norelax
  la gp, __global_pointer$
  .option pop                          # Restore the previous assembler options

#if __riscv_xlen == 64
  # Rocket cores reset mtvec to 0, which holds another core's code in the shared L1.
  # Trap into a local loop instead; mepc and mcause keep the trap state.
  la      t0, 13f
  csrw    mtvec, t0
#endif

/* set stack pointer */
  la sp, __stack_top

  # Set the thread pointer to the base of the per-RISC thread_local region.
  # A `thread_local` variable is accessed as tp + tprel_offset, and the linker
  # places the TLS block at the region origin (__thread_local_start), so this
  # makes those accesses resolve to the variable's slot in REGION_THREAD_LOCAL.
  la tp, __thread_local_start

  # Clear the thread_local .tbss span. The rest of .thread_local (initialized
  # .tdata and the __attribute__((section(".thread_local"))) form) is written
  # directly by the loader, so only the .tbss bytes need zeroing here.
  la      t0, __thread_local_bss_start # Load the address of __thread_local_bss_start into t0
  la      t1, __thread_local_bss_end   # Load the address of __thread_local_bss_end into t1
11:beq    t0, t1, 12f                  # If t0 == t1, break out of loop
  sw      zero, 0(t0)                  # Store 0 at address pointed by t0
  addi    t0, t0, 4                    # Move to the next word (32-bit) address
  j       11b                          # Jump back to label 11
12:

  # Clear the bss segment
  la      t0, __ldm_bss_start          # Load the address of __ldm_bss_start into t0
  la      t1, __ldm_bss_end            # Load the address of __ldm_bss_end into t1
4:beq     t0, t1, 5f                   # If t0 == t1, break out of loop
  sw      zero, 0(t0)                  # Store 0 at address pointed by t0
  addi    t0, t0, 4                    # Move to the next word (32-bit) address
  j       4b                           # Jump back to label 4

  # Copy memory from .loader_init to .ldm_data
5:la      t0, __loader_init_start      # Load the address of __loader_init_start into t0
  la      t1, __loader_init_end        # Load the address of __loader_init_end into t1
  beq     t0, t1, 7f                   # If t0 == t1, skip; nothing should be loaded into L0
  la      t1, __ldm_data_end           # Load the address of __ldm_data_end into t1
  la      t2, __ldm_data_start         # Load the address of __ldm_data_start into t2
6:beq     t2, t1, 7f                   # If t2 == t1, break out of loop
  lw      t3, 0(t0)                    # Load word from .loader_init
  sw      t3, 0(t2)                    # Store word to .ldm_data
  addi    t0, t0, 4                    # Move to the next word in .loader_init
  addi    t2, t2, 4                    # Move to the next word in .ldm_data
  j       6b                           # Jump back to label 6

  # Execute global initialization
7:la      s2, __init_array_start       # Load the address of __init_array_start into s2
  la      s3, __init_array_end         # Load the address of __init_array_end into s3
  j       9f                           # Jump to label 9
8:REG_L   a0, 0(s2)                    # Load the function pointer at s2 into a0
  jalr    a0                           # Jump and link register to the address in a0
  addi    s2, s2, SZREG                # Move to the next pointer in the init array
9:bne     s2, s3, 8b                   # If s2 != s3, jump back to label 8

  /* Pass in the tensix coordinates as argv[0][0] through argv[0][3].
     argc = 1, envp = NULL. In memory, we'll have
   * sp+0:         argv[0] -> sp+2*SZREG
   * sp+SZREG:     argv[1] = NULL
   * sp+2*SZREG:   s1
   * sp+2*SZREG+4: 0
   */
  addi    sp, sp, -4*SZREG /* (stack is aligned to 16 bytes in riscv calling convention) */
  addi    a0, sp, 2*SZREG
  REG_S   a0, 0(sp)
  REG_S   zero, SZREG(sp)
  sw      s1, 2*SZREG(sp)
  sw      zero, 2*SZREG+4(sp)

  li      a0, 1 # argc = 1
  mv      a1, sp
  mv      a2, zero

  # Init coverage section so host knows it exists
  #ifdef COVERAGE
  call gcov_init
  #endif

  call    main

  # Automatically dump gcda into L1 when main returns if built with coverage.
  #ifdef COVERAGE
  call gcov_dump
  #endif

  # Loop infinitely.
  10: j 10b

#if __riscv_xlen == 64
  # Trap loop that mtvec points to (direct mode needs a 4-byte aligned address).
  .align 2
  13: j 13b
#endif

  .size  _start, .-_start

  .global _init
  .type   _init, @function
  .global _fini
  .type   _fini, @function
_init:
_fini:
  # These don't have to do anything since we use init_array/fini_array.
  ret
  .size  _init, .-_init
  .size  _fini, .-_fini
