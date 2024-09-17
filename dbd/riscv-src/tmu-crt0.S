.section .init
.global _start
.type   _start, @function

_start:

CRT_START:
  # Initialize global pointer
  .option push
  .option norelax
1:auipc gp, %pcrel_hi(__global_pointer$)
  addi  gp, gp, %pcrel_lo(1b)

/* set stack pointer */
  la sp, __stack_top

  # Clear the bss segment
  la      t0, __ldm_bss_start  # Load the address of __ldm_bss_start into t0
  la      t1, __ldm_bss_end    # Load the address of __ldm_bss_end into t1
3:beq     t0, t1, 4f           # If t0 == t1, break out of loop
  sw      zero, 0(t0)          # Store 0 at address pointed by t0
  addi    t0, t0, 4            # Move to the next word (32-bit) address
  j       3b                   # Jump back to label 3

  # Execute global initialization
4:la      s2, __init_array_start
  la      s3, __init_array_end
  j       6f
5:lw      a0, 0(s2)
  jalr    a0
  addi    s2, s2, 4
6:bne     s2, s3, 5b
  .option pop

  /* Pass in the tensix coordinates as argv[0][0] through argv[0][3].
     argc = 1, envp = NULL. In memory, we'll have
   * sp+0: argv[0] -> sp+8
   * sp+4: argv[1] = NULL
   * sp+8: s1
   * sp+c: 0
   */
  addi    sp, sp, -16 /* (stack is aligned to 16 bytes in riscv calling convention) */
  addi    a0, sp, 8
  sw      a0, 0(sp)
  sw      zero, 4(sp)
  sw      s1, 8(sp)
  sw      zero, 12(sp)

  li      a0, 1 # argc = 1
  mv      a1, sp
  mv      a2, zero

  call    main
  tail    exit
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
