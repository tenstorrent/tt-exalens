# Test coverage analysis with gcov

## Tutorial

If you wish to get coverage info for your kernels:
- Make the build changes as demonstrated in `riscv-src/*.ld` and `riscv-src/CMakeLists.txt`. This comes down to ensuring your memory layout can handle this (increase code/data sections as needed, free up L0), compiling with coverage and `-fprofile-info-section`, linking with the routines from `coverage.c` and `gcov.c`, and running `gcov_dump` at the end of your kernels (see the end of `tmu-crt0.S`: ensure it is present in your C runtime, or call `gcov_dump` at the end of each kernel manually).
- After the kernel completes, pull its gathered coverage data with the `dump-coverage` (`cov`) command in tt-exalens: specify the path to the executed ELF, the output gcda path, and optionally the output gcno path.
- Once you've done that for all kernels, use any tool you wish to process the gathered data. `lcov` is one of them.

The latter two steps, for a simple run with two kernels, may go as follows:

In exalens (or in a script with equivalent functionality using `tt-exalens-lib`):

```
re build/riscv-src/wormhole/sample.coverage.trisc0.elf -r trisc0
re build/riscv-src/wormhole/callstack.coverage.trisc2.elf -r trisc2

cov build/riscv-src/wormhole/run_elf_test.coverage.trisc0.elf coverage_dir/run_elf_test.gcda coverage_dir/run_elf_test.gcno
cov build/riscv-src/wormhole/cov_test.coverage.trisc2.elf coverage_dir/cov_test.gcda coverage_dir/cov_test.gcno
```

And in the shell:
```bash
./scripts/merge-coverage.sh coverage_dir cov_report
```

Then just open `cov_report/index.html`.
You can of course run the commands in one `tt-exalens --command` invocation (commands are separated by semicolons):
```bash
./tt-exalens --command "re foo.elf -r trisc0;cov foo.elf foo.gcda foo.gcno;x"
```
Note the `x` at the end: it tells tt-exalens to exit instead of dropping you into an interactive session.

Note:
- As each RISC has its own coverage region, it's fine to run instrumented kernels in parallel and grab data from each one.
- Don't try instrumenting with `-fprofile-topn` or `-fprofile-values`, these may require runtime heap allocation. In case those options are ever needed, make sure you link in `write_topn_counters` from `libgcov-driver.c` and write a heap allocator. The allocation function must be passed to `__gcov_info_to_gcda`.
- As is mentioned later in this file, currently only one TU can be instrumented per kernel. This is so for the sake of simplicity.

## Overview

When compiling for coverage, GCC does the following:
- Allocates space in the executable for profiling counters that get incremented as code executes.
- Instruments the code with instructions to increment the counters: most basic blocks have a counter which they bump when they are executed.
- Generates at compile time gcno (note) files for each translation unit. They describe that unit's CFG, which branches and blocks exist, and what the overall structure of the code looks like. The note files let the compiler map the raw counters back to the source code.
- Inserts a call at program exit to collect the counters and pack them into a gcda (data) file which then contains that run's profiling and coverage data.

Afterwards, tools like gcov and lcov can use the gcno-gcda pair to produce a coverage report.

## Documentation

Under the hood, GCC’s profiling and coverage machinery presupposes two things: global constructors and destructors that initialize and dump the counters, and a filesystem to store the gcda files at program exit. Neither presupposition holds for us.

However, GNU gentlemen had a usecase such as this in mind, so they provided the [-fprofile-info-section](https://gcc.gnu.org/onlinedocs/gcc-15.1.0/gcc/Freestanding-Environments.html) compiler flag, which makes it relatively straightforward to make profiling and coverage work on freestanding devices without having to resort to hacks like semihosting. The basic idea is removing the need for global constructors (to initialize the counters) and destructors (to dump the gathered data), and instead statically initializing the data and letting the programmer walk the counters manually to extract them over any medium of communication at his disposal.

The compiler accomplishes this by essentially cramming the coverage counters into `.bss`, turning off the global ctors and dtors (in `.init`/`.init_array`, `.fini`/`.fini_array`) for gcov stuff, and exposing a pair of iterators (`__gcov_info_start` and `__gcov_info_end`) which point to per-TU data (`struct gcov_info`).

Making gcov work on our hardware involved a few things:
1. Compiling with `-fprofile-arcs -ftest-coverage -fprofile-info-section`
2. Exposing the data in L1
3. Extracting the data onto the host system

---

### 1. Compiling

This is a lot more involved beyond mechanically adding the compiler flags and typing `make`.

Just telling GCC to compile with `-fprofile-arcs -ftest-coverage -fprofile-info-section` will pull in libgcov, which then pulls in the entirety of the C standard library I/O (from newlib), which made my first attempt at compiling fail spectacularly (with 60KiB+ `.text` section overflows).

Linker script adjustments were immediately necessary. The private memory region (or L0 if you will) got bloated, so I placed it into L1 and let only the stack reside in L0. I also added a new region where the coverage data stream in gcda format will be written into, and hacked together a minimal library for extracting coverage data; more on those topics in **2**.

If you skim through the tutorial provided in the GCC docs linked above, you may notice they note some linker script changes necessary for `-fprofile-info-section` to work:

```GNU ld
.gcov_info :
  {
    PROVIDE (__gcov_info_start = .);
    KEEP (*(.gcov_info))
    PROVIDE (__gcov_info_end = .);
  }
```

I have noticed that the `PROVIDE` directive does not get the job done for us, so I exposed the symbol with the plain `__gcov_info_start = .` statement. Mind that the `KEEP` directives are necessary for the linker to not discard this section as unused.

More linker script tweaks may be necessary depending on the nature of the instrumented kernels. In case there's an overflow in `.text` or some other such problem, simply expanding the region should get the job done. The numbers present in my scripts are more than sufficient for anything I've tested with.

---

### 2. Converting counters into gcda and exposing it

libgcov provides `__gcov_info_to_gcda` (found in `gcc/libgcc/libgcov-driver.c`) which converts raw counter info into the gcda format that can later be used by tools like `gcov` and `lcov`. However, as already mentioned, linking against libgcov turned out to be a problem (as we don't want all of newlib). That function itself does not have any libc dependencies, so I copied the minimal required implementation of `__gcov_info_to_gcda` and its dependencies from GCC's codebase into `gcov.c`, which should then be linked into kernels compiled for coverage.

The counters for each kernel, its pointer to the `struct gcov_info`, and the struct itself, are all in its `.ldm_data` (the counter being in the `bss` portion, unlike the other two). When the kernel ends, the C runtime `tmu-crt0.S` calls `gcov_dump`, which passes that pointer to `__gcov_info_to_gcda`, which then gives us a data stream in gcda format. The linker scripts define `REGION_GCOV` (as well as two symbols to access it: `__coverage_start` and `__coverage_end`), and we write a short header and then the data stream as a byte array into that region.

There is no need to iterate from `__gcov_info_start` to `__gcov_info_end` as only one `struct gcov_info` is present (since this was built with only one TU per kernel in mind). This also simplifies more things that the tutorial mentions - `gcov-merge-tool` is unnecessary, and so is the filename prefix function (for the most part). Namely, that function (`coverage.c:filename`) receives the filename string from `struct gcov_info`, which is the expected output path for the gcda, and it will be in the same directory as where the compiler placed the gcno. We use this to later find the gcno if so asked. `filename` merely writes the pointer it receives and the length of the string into the second and third word in the region, respectively. To be clear, this is not a requirement of the gcda format; this is done to make `cov` calls simpler and safer.

The layout of the coverage region is as follows (in word granularity, i.e. 4 bytes):
  
```
REGION_GCOV (__coverage_start...__coverage_end)
- [0] length in bytes of the data in the region (including the header)
- [1] pointer to the filename (`struct gcov_info.filename`)
- [2] length of the filename string
- [3...] gcda data stream
```

---

### 3. Storing the data on the host

`tt-exalens` can extract the data for you with the `dump-coverage` (or `cov`) command. You merely supply the path to the currently running ELF for which you want to gather coverage data, and where you want to output it. Optionally you may provide where you want the original gcno (inferred from `struct gcov_info.filename`) to be placed. It walks the symbol table, finds `__coverage_start`, reads the header (length, filename pointer, `strlen(filename)`) and extracts the gcda and optionally gcno. When you've run this command for every ELF whose coverage you wanted, you may wish to run `scripts/merge-coverage.sh` on the directory with the gcno-gcda pairs, which will call `lcov` and `genhtml` for you so that you can just open the html afterwards.
