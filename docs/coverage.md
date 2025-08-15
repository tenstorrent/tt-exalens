# Test coverage analysis with gcov

## Tutorial

If you wish to get coverage info for your kernels:
- Make the build changes as demonstrated in `riscv-src/*.ld` and `riscv-src/CMakeLists.txt`.
- Include `coverage.h` and call `gcov_dump` at the end of each kernel, just before the infinite loop.
- After the kernel completes, pull its gathered coverage data with `./tt-exalens --command (finish this later)`: specify the running ELF itself, the gcno file (typically in the same directory as the kernel's object file), and the directory into which it should be written.
- Once you've done that for all kernels, use any tool you wish to process the gathered data. `lcov` is one of them.

The latter two steps, for a simple run with three kernels, may go as follows:

(update this later)

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
python covmerge.py coverage_dir cov_report
```

Then just open `cov_report/index.html`.

Note:
- As each RISC has its own coverage region, it's fine to run instrumented kernels in parallel and grab data from each one.
- Running `covdump.py` on a currently halted RISC might mess up the board state so bad you need to restart the whole machine.
- Don't try instrumenting with `-fprofile-topn` or `-fprofile-values`. In case that is ever needed, adjust write_topn_counters in `tt-gcov.c` and write a heap allocator.

## Documentation

*(preliminary documentation)*

The problem with GCC's profiling and test coverage out of the box for us is its reliance on a filesystem.

However, GNU gentlemen had a usecase such as this in mind, so they provided the [-fprofile-info-section](https://gcc.gnu.org/onlinedocs/gcc-15.1.0/gcc/Freestanding-Environments.html) compiler flag, which makes it relatively straightforward to make profiling and coverage work on non-hosted devices without having to resort to hacks like semihosting. The basic idea is removing the need for global constructors (to initialize the counters) and destructors (to dump the gathered data), and instead statically initializing the data and letting the programmer walk the counters manually to extract them over any medium of communication at his disposal.

The compiler accomplishes this by essentially cramming the coverage counters into .bss, turning off the global ctors and dtors (in `.init`/`.init_array`, `.fini`/`.fini_array`) for gcov stuff and exposing a pair of iterators (`__gcov_info_start` and `__gcov_info_end`) which point to per-TU data.

Making gcov work on our hardware involved a few things:
1. Compiling with `-fprofile-arcs -ftest-coverage -fprofile-info-section`
2. Exposing the data in L1
3. Extracting the data from the host system

---

### 1. Compiling

This involved quite a lot more beyond mechanically adding the compiler flags and typing `make`.

Just telling GCC to compile with `-fprofile-arcs -ftest-coverage -fprofile-info-section` will pull in libgcov, which then pulls in the entirety of the C standard library I/O (from newlib), which made my first attempt at compiling fail spectacularly.

Linker script adjustments were immediately necessary. Much of the things that would end up in the private memory region (or L0 if you will; the `0xFFB...` region) were pulled out of there, chiefly the whole .bss segment, where the (implicitly) zero-initialized counters ended up in. Further, it turns out that something in the build process in the exalens repo (from which I was doing this) pulls in `errno` (I've confirmed this is the case without my changes), and our linker scripts allow that, which in turn pulls in loads of reentrancy machinery from newlib and bloats L0. That was extracted out of there and placed in L1 - the `REGION_IMPURE_DATA` ld script entries (it'd be safe to just kick it out entirely, but that was outside the scope of this project). Linking against libgcov directly was thus infeasible; the exact plan for that is laid out in 2.

If you skim through the tutorial provided in the GCC docs linked above, you may notice the linker script adjustments they talk about for use with `-fprofile-info-section`. I have noticed that the `PROVIDE` directive does not get the job done for us, so I exposed the symbol with the plain `__gcov_info_start = .` statement. Mind that the `KEEP` directives are necessary.

More linker script adjustments may be necessary depending on the nature of the instrumented kernels. In case there's an overflow in `.text` or some other such problem, simply expanding the segment should get the job done. The numbers present in my scripts are more than sufficient for anything I've tested with (and they're quite generous; they could be significantly trimmed down if L1 turns out to be scarce).

---

### 2. Converting counters into gcda and exposing it

libgcov provides `__gcov_info_to_gcda` (found in `gcc/libgcc/libgcov-driver.c`) which converts raw counter info into the gcda format that can later be used by tools like `gcov` and `lcov`. However, linking against libgcov turned out to be a problem (as we don't want all of newlib). That function itself does not have any libc dependencies, so I did the simplest thing and just carved it out, rather unceremoniously, along with its dependencies out of GCC's codebase and compiled it as a separate static library (found in `tt-gcov.c`).

The counters for each kernel are in its `.bss`, and the pointer to the `struct gcov_info` is in `REGION_GCOV_INFO` (the struct itself lives in `.data`; it contains a pointer to the counters in `.bss`). The pointer is passed to `__gcov_info_to_gcda`, which then gives us a data stream in gcda format. The linker scripts also define `REGION_GCOV` (as well as two symbols to access it: `__coverage_start` and `__coverage_end`), and we write the data stream as a length-prefixed byte array into that region.

---

### 3. Storing the data on the host

A convenience script for extracting the gcda from the device is in `tt-exalens/ttexalens/riscv-src/coverage`: `covdump.py`. You merely supply it the path to the currently running ELF for which you want to gather coverage data, and where you want to output it. It walks the symbol table, finds `__coverage_start`, reads the length prefix and then reads the gcda into a file. It also finds the corresponding gcno and puts it next to the gcda. When you've run this script for every ELF whose coverage you wanted, you run `covmerge.py` on the directory with the gcno-gcda pairs, which will call `lcov` and `genhtml`. Afterwards, just open the html.
