# Test coverage analysis with gcov

## Tutorial

If you wish to get coverage info for your kernels:
- Make the build changes as demonstrated in `riscv-src/*.ld` and `riscv-src/CMakeLists.txt` (this comes down to ensuring your memory layout can handle this, compiling with coverage and -fprofile-info-section, linking with the libraries, and running `gcov_dump` at the end of your kernels).
- After the kernel completes, pull its gathered coverage data with `./tt-exalens --command "cov <core-loc> <elf> <outdir>;x"`: specify the running ELF itself, and the directory into which it should be written.
- Once you've done that for all kernels, use any tool you wish to process the gathered data. `lcov` is one of them.

The latter two steps, for a simple run with three kernels, may go as follows:

In exalens (or in a script with equivalent functionality using `tt-exalens-lib`):

```
re build/riscv-src/wormhole/sample.coverage.trisc0.elf -r trisc0
re build/riscv-src/wormhole/callstack.coverage.trisc2.elf -r trisc2
```

In the shell:

```bash
./tt-exalens --command "cov 0,0 build/riscv-src/wormhole/sample.coverage.trisc0.elf build/obj/riscv-src/sample.gcno coverage_dir;x"
./tt-exalens --command "cov 0,0 build/riscv-src/wormhole/callstack.coverage.trisc2.elf build/obj/riscv-src/callstack.gcno coverage_dir;x"
./scripts/merge-coverage.sh coverage_dir cov_report
```

Then just open `cov_report/index.html`.
You can of course run both `cov` calls in one `tt-exalens --command` invocation; commands are separated by semicolons.

Note:
- As each RISC has its own coverage region, it's fine to run instrumented kernels in parallel and grab data from each one.
- Don't try instrumenting with `-fprofile-topn` or `-fprofile-values`. In case that is ever needed, make sure you link in `write_topn_counters` from `libgcov-driver.c`, and write a heap allocator.

## Documentation

The problem with GCC's profiling and test coverage out of the box for us is its reliance on a filesystem.

However, GNU gentlemen had a usecase such as this in mind, so they provided the [-fprofile-info-section](https://gcc.gnu.org/onlinedocs/gcc-15.1.0/gcc/Freestanding-Environments.html) compiler flag, which makes it relatively straightforward to make profiling and coverage work on non-hosted devices without having to resort to hacks like semihosting. The basic idea is removing the need for global constructors (to initialize the counters) and destructors (to dump the gathered data), and instead statically initializing the data and letting the programmer walk the counters manually to extract them over any medium of communication at his disposal.

The compiler accomplishes this by essentially cramming the coverage counters into .bss, turning off the global ctors and dtors (in `.init`/`.init_array`, `.fini`/`.fini_array`) for gcov stuff, and exposing a pair of iterators (`__gcov_info_start` and `__gcov_info_end`) which point to per-TU data.

Making gcov work on our hardware involved a few things:
1. Compiling with `-fprofile-arcs -ftest-coverage -fprofile-info-section`
2. Exposing the data in L1
3. Extracting the data from the host system

---

### 1. Compiling

This involved quite a lot more beyond mechanically adding the compiler flags and typing `make`.

Just telling GCC to compile with `-fprofile-arcs -ftest-coverage -fprofile-info-section` will pull in libgcov, which then pulls in the entirety of the C standard library I/O (from newlib), which made my first attempt at compiling fail spectacularly.

Linker script adjustments were immediately necessary. The private memory region (or L0 if you will) got bloated, so I placed it into L1 and let only the stack reside in L0. I also added a new region in which the gcda will be placed; more on that in 2.

If you skim through the tutorial provided in the GCC docs linked above, you may notice the linker script changes they talk about for use with `-fprofile-info-section`. I have noticed that the `PROVIDE` directive does not get the job done for us, so I exposed the symbol with the plain `__gcov_info_start = .` statement. Mind that the `KEEP` directives are necessary.

More linker script adjustments may be necessary depending on the nature of the instrumented kernels. In case there's an overflow in `.text` or some other such problem, simply expanding the region should get the job done. The numbers present in my scripts are more than sufficient for anything I've tested with.

---

### 2. Converting counters into gcda and exposing it

libgcov provides `__gcov_info_to_gcda` (found in `gcc/libgcc/libgcov-driver.c`) which converts raw counter info into the gcda format that can later be used by tools like `gcov` and `lcov`. However, as already mentioned, linking against libgcov turned out to be a problem (as we don't want all of newlib). That function itself does not have any libc dependencies, so I did the simplest thing and just carved it out, rather unceremoniously, along with its dependencies out of GCC's codebase and compiled it into a separate object file (found in `gcov.c`), which should then be linked into kernels compiled for coverage.

The counters for each kernel, its pointer to the `struct gcov_info`, and the struct itself, are all in its `.ldm_data` (the counter being in the `bss` portion, unlike the other two). When the kernel ends, the C runtime `tmu-crt0.S` calls `gcov_dump`, which passes that pointer to `__gcov_info_to_gcda`, which then gives us a data stream in gcda format. The linker scripts define `REGION_GCOV` (as well as two symbols to access it: `__coverage_start` and `__coverage_end`), and we write the data stream as a length-prefixed byte array into that region.

There is no need to iterate from `__gcov_info_start` to `__gcov_info_end` as only one `struct gcov_info` is present (since there's only one TU per kernel). This also simplifies more things that the tutorial mentions - `gcov-merge-tool` and the filename prefix function are unnecessary.

The layout of the coverage region is as follows:
- first word contains the length in bytes of the data in the region
- second word contains the pointer to the filename (`struct gcov_info.filename`)
- third word contains the length of the filename string
- fourth word and onwards is the gcda data stream.

---

### 3. Storing the data on the host

`tt-exalens` can extract the data for you with the `dump-coverage` (or `cov`) command. You merely supply the path to the currently running ELF for which you want to gather coverage data, and where you want to output it. Optionally you may provide where you want the original gcno (inferred from `struct gcov_info.filename`) to be placed. It walks the symbol table, finds `__coverage_start`, reads the header (length, filename pointer, `strlen(filename)`) and extracts the gcda and optionally gcno. When you've run this script for every ELF whose coverage you wanted, you may wish to run `scripts/merge-coverage.sh` on the directory with the gcno-gcda pairs, which will call `lcov` and `genhtml` for you so that you can just open the html afterwards.
