# Stack independent llk testing infrastructure (wip)

## Quickstart

Make sure you are using default buda docker image

- Clone debuda
- Checkout lpremovic/llk-tests
- Update submodules
- `pip install -r dbd/requirements.txt`
- `make build`
- `cd llk_test/ && make dis && cd ..`
- `./llk.sh`

Last memory readout should contain 0xF0000000 - 0xF00003FF

## Explanation

### tt_llk_wormhole_b0 submodule

tt_llk_wormhole_b0 submodule was added as it contains API-s being tested.  
It was also modified such that there is a 1024 word instruction_trace buffer with write pointer allocated in L1 for each core
which TT\_ and TTI\_ instructions use to store instruction words after sending them to tensix thus providing a trace of all instructions sent to tensix.

### Code organization

Most of the testing specific files are stored in `llk_test`, Makefile provided there is used for building test binaries along with the contents of `llk_test/helpers` directory (main c file, linker script and startup code), they are both derived from similar files in budabackend and files used for testing run-elf command in debuda.

Tests are stored in `llk_test/tests` and should consist of one .py and one .cpp file, currently there is only one cpp file for the example test, planned test structure as opposed to whats currently implemented will be explained later.

Test cpp file should contain one `void run_kernel()` implementation for each core, guarded with proper ifdef (LLK\_TRISC\_UNPACK, LLK\_TRISC\_MATH or LLK\_TRISC\_PACK), inside that function unit test kernel should be implemented using \_llk\_\*\_  calls.

Files that llk or parts of budabackend that haven't been decoupled yet depend on are copied from budabackend and placed in `third_party/firmware`, one of the next steps should be taking a look at and pruning all dependencies that can easily be decoupled.

The script for running the example test `llk.sh` is stored in the root of repository along with utility files for interpreting tensix instruction trace `llkd.*`.

### Running the example test

After being compiled by running `make dis` in `llk_test` (which also copies test cpp to build dir as `llk.cpp`, note that test to be copied is currently hardcoded), test can be run using a hardcoded script `llk.sh` in the root of the repository.

`llk.sh` uses debuda's command line interface to do the following:

- reset all RISCs
- read first word of input and output buffers to verify that they have garbage values before the test is executed
- load appropriate elf's on TRISCs
- take all RISCs out of reset
- read the status of all TRISCs to verify that they are executing
- read l1 mailbox of all TRISCs to verify that the kernels completed successfully or to look at breadcrumbs to see where the hang happened (if kernels has completed successfully the mailbox value should be 1)
- read tensix instruction trace pointer to figure out how many instructions have been issued to tensix
- read tensix instruction trace buffer to see instruction words of all instructions issued to tensix from a particular core (only first instruction trace pointer words contain meaningful values)
- two steps above are repeated for all TRISCs
- read the complete contents of input buffer in l1
- read the complete contents of output buffer in l1

Since the example only does int32 unpack to dest and in32 pack the contents of input and output buffers should be identical

Note that elf paths and more importantly memory addresses are hardcoded and have to be updated by hand from objdump when test is changed.

Also note that this branch uses the run-elf command with workarounds for debug_enable hardware bug, while the main branch should have a new loader implemented that does not need this workaround, for more details on the workaround take a look at debuda PR #88.

### Planned test structure

While the current proof of concept is quite crude, further plans for test structure have been elaborated and will be presented here.

What is definitely missing from current proof of concept is stimulus/golden generation and output comparison, these parts were meant to be implemented as a part of python file accompanying each test.

Each python file would represent a test or a set of tests that are being run with `.cpp` file of the same name. Test would be collected and run using pytest and each test would do the following:

- copy and compile corresponding `.cpp` kernel
- generate stimulus
- compute golden
- write stimulus to l1
- run steps similar to `llk.sh` (resetting RISCs, loading firmware and clearing reset)
- read output from l1
- compare output and golden

Steps currently implemented in `llk.sh` should be converted to use newly implemented debuda library instead of command line scripting.

Hardcoded addresses need to be removed and that can either be done by scanning output of objdump for signal values or by having certain symbols fixed at certain addresses in linker script.

## Tracing tensix instructions

Once `llk.sh` has dumped hex values of instructions sent to tensix, it would be useful to be able to analyze that data in human readable format. For that we can leverage sfpi compiler's objdump whose disassembly will correctly decode tensix instructions, meaning that we need to get our hex values disassembled by sfpi objdump. Easiest way to do that is by populating a c array with those values, and compiling then disassembling that file

That is exactly what `llkd.c` and `llkd.sh` are for, paste values from trace buffers into an array in `llkd.c` and run `llkd.sh` which will compile and disassemble `llkd.c` into `llkd.dmp` where we can look at tensix instructions in human readable format
