# Test coverage analysis with gcov

## Tutorial

If you wish to get coverage info for your kernels:
- Make the build adjustments as demonstrated in [my branch](https://github.com/tenstorrent/tt-exalens/compare/iklikovac/coverage) (compiler flags and ld script changes), include `ttgcov-runtime.h`, and call `gcov_dump` at the end of each kernel, just before the infinite loop.
- After the kernel runs, pull its gathered coverage data with `covdump.py`: specify the running ELF itself, the gcno file (typically in the same directory as the kernel's object file), and the directory into which it should be written.
- Once you've done that for all kernels, run `covmerge.py` and open `index.html` located in the directory you specified.
  
The latter two steps, for a simple manual run with three kernels, may go as follows:
  
In exalens:
  
```
re build/riscv-src/wormhole/sample.trisc0.elf -r trisc0
re build/riscv-src/wormhole/callstack.trisc1.elf -r trisc1
re build/riscv-src/wormhole/cov_test.trisc2.elf -r trisc2
```
  
In the shell:
  
```bash
python covdump.py build/riscv-src/wormhole/sample.trisc0.elf build/obj/riscv-src/sample.gcno coverage_dir
python covdump.py build/riscv-src/wormhole/callstac.trisc1.elf build/obj/riscv-src/callstack.gcno coverage_dir
python covdump.py build/riscv-src/wormhole/cov_test.trisc2.elf build/obj/riscv-src/cov_test.gcno coverage_dir
python covmerge.py coverage_dir coverage_results coverage_dir/final.info
```
  
Then just open `coverage_results/index.html`.

Mind that running `covdump.py` on a currently halted RISC might mess up the board state so bad you need to restart the whole machine.

## Documentation

*(preliminary documentation)*

The problem with GCC's profiling and test coverage out of the box for us is its reliance on a filesystem.
  
However, GNU gentlemen had a usecase such as this in mind, so they provided the [-fprofile-info-section](https://gcc.gnu.org/onlinedocs/gcc-15.1.0/gcc/Freestanding-Environments.html) compiler flag, which makes it relatively straightforward to make profiling and coverage work on non-hosted devices without having to resort to hacks like semihosting. The basic idea is removing the need for global constructors (to initialize the counters) and destructors (to dump the gathered data), and instead statically initializing the data and letting the programmer walk the counters manually to extract them over any medium of communication at his disposal.
  
The compiler accomplishes this by essentially cramming the coverage counters into .bss, turning off the global ctors and dtors (in `.init`/`.init_array`, `.fini`/`.fini_array`) for gcov stuff and exposing a pair of iterators (`__gcov_info_start` and `__gcov_info_end`) which point to per-TU data.
  
Making gcov work on our hardware involved several things:
1. Compiling with `-fprofile-arcs -ftest-coverage -fprofile-info-section`
2. Linking against the GCC-provided routines for raw counter -> gcda conversion
3. Writing a small runtime library that exposes the gcda in L1
4. Extracting the data from the host system
5. Processing it
  
### 1. Compiling

This involved a lot more beyond mechanically adding the compiler flags and typing `make`.
  
Just telling GCC to compile with `-fprofile-arcs -ftest-coverage -fprofile-info-section` will pull in libgcov, which then pulls in the entirety of the C standard library (through newlib), which made my first attempt at compiling fail spectacularly.
  
Linker script adjustments were immediately necessary. Much of the things that would end up in the private memory region (or L0 if you will; the 0xFFB... region) were pulled out of there, chiefly the whole .bss segment, where the (implicitly) zero-initialized counters ended up in. Further, it turns out that something in the build process in the exalens repo (from which I was doing this) pulls in `errno` (I've confirmed this is the case without my changes), and our linker scripts allow that, which in turn pulls in loads of reentrancy machinery from newlib and bloats L0. That was extracted out of there and placed in L1 - the IMPURE_DATA ld script entries. Linking against libgcov directly was thus infeasible; the exact plan for that is laid out in 2.
  
If you skim through the tutorial provided in the GCC docs linked above, you may notice the linker script adjustments they talk about for use with `-fprofile-info-section`. I have noticed that the `PROVIDE` directive does not get the job done for us, so I exposed the symbol with the plain `__gcov_info_start = .` construct. Mind that the `KEEP` directives are necessary.
  
More linker script adjustments may be necessary depending on the nature of the instrumented kernels. In case there's an overflow in .text or some other such problem, simply expanding the segment should get the job done. The numbers present in my scripts are more than sufficient for anything I've tested with (and they're quite generous; they could be significantly trimmed down if L1 turns out to be scarce.)

### 2. gcda conversion

libgcov provides __gcov_info_to_gcda (found in gcc/libgcc/libgcov-driver.c) which converts raw counter info into the gcda format that can later be used by tools like gcov and lcov. However, linking against libgcov turned out to be a problem (we don't want all of newlib). That function itself does not have any libc dependencies, so I did the simplest thing and rather unceremoniously carved it out along with its dependencies out of the source file and compiled it as a separate static library (found in tt-gcov.c).