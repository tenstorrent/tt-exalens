## Architecture

Each tenstorrent chip has many tensix cores. Each tensix core has couple of riscv cores that can be debugged. Since each riscv core has its own private memory and code that is being executed, gdb server exposes every riscv core as a separate process that can be debugged.

ttexalens application is hosting gdb server. You should use gdb client to connect to gdb server and you need to enable multiprocess debugging to be able to debug multiple cores at the same time.

## Starting gdb server

You can start gdb server with ttexalens application:

- With command line argument: Start ttexalens with `--start-gdb=<gdb_port>` where `<gdb_port>` is integer number for port that will be used for gdb server.
- With `gdb` command: After you start ttexalens, you can use `gdb` command to start gdb server. Run `gdb start --port <port>` where `<port>` is integer number of port that will be used for gdb server.

After starting gdb server, you can stop it with `gdb` command. Run `gdb stop`.

## Getting gdb client

There are a few ways to obtain the GDB client:
- Use the version that is automatically downloaded and extracted during the build process at `build/sfpi/compiler/bin/riscv-tt-elf-gdb`.
- Install sfpi on your system (the deb package installs to `/opt/tenstorrent/sfpi`).
- Download your preferred version manually from https://github.com/tenstorrent/sfpi or build it yourself from source.

The GDB client is **not** bundled in the wheel, since the binary is not portable across platforms. `tt-exalens --gdb` (a wrapper that starts the GDB client) and the call-stack support locate the client by searching, in order:
1. The package's own `sfpi/compiler/bin/riscv-tt-elf-gdb` (in-tree layout).
2. The local development build at `build/sfpi/compiler/bin/riscv-tt-elf-gdb`.
3. The system install at `/opt/tenstorrent/sfpi/compiler/bin/riscv-tt-elf-gdb`.
4. `$SFPI_ROOT/compiler/bin/riscv-tt-elf-gdb` (set `SFPI_ROOT` to your sfpi install root).
5. `riscv-tt-elf-gdb` on your `PATH`.

## Connecting gdb client

- Start the GDB client.
- To debug client/server communication, run `set debug remote 1` in the GDB client.
- Connect the GDB client to the debugger using: `target extended-remote localhost:<gdb_port>`.

After connection has been established, you can use `info os processes` to list all available processes that you can debug with GDB. Use `attach <pid>` to start debugging selected riscv core.

## Loading elf and getting call stack

Once attached to the process, you can load the ELF file using the `add-symbol-file <path-to-elf> [<offset>]` command. The `<path-to-elf>` is a required argument specifying the path to the ELF file of the program you want to debug. The `<offset>` is an optional argument indicating the address where the program is loaded in memory.

After the symbols are loaded, you can display the call stack using the `bt` (backtrace) command.

## Sample app debugging script:

Once you started gdb server, you can use run-elf command to execute `ttexalens/riscv-src/sample.cc` application on chip. For wormhole, you can execute `re build/riscv-src/wormhole/sample.brisc.elf` to run application on brisc core.

After that, you can execute this example script in gdb client to debug it:

```
# Print g_MAILBOX as hex and verify its value is 0xffb1208c
print/x g_MAILBOX

# Set g_MAILBOX to 0x1234 so code passes to next checkpoint
set variable g_MAILBOX = 0x1234

# Continue executing code
continue

# Now example code will continue until the point it self halts with ebreak
# Print g_MAILBOX as hex and verify its value is 0xffb12080
print/x g_MAILBOX

# Set a breakpoint at function decrement_mailbox
break decrement_mailbox

# Set memory watchpoints
watch g_TESTBYTEACCESS.bytes[3]
watch g_TESTBYTEACCESS.bytes[5]
watch g_TESTBYTEACCESS.low_32
watch g_TESTBYTEACCESS.high_32

# Continue executing code
continue

# We will now stop in decrement_mailbox three times in a loop, so we need to continue 3 times
# You can verify g_MAILBOX value to see how many more times we will break in decrement_mailbox
print g_MAILBOX
continue
continue
continue

# Next are memory watchpoints
# You should see messages regarding variables that changed value, so you could print only g_MAILBOX to verify it
# Print g_MAILBOX as hex and verify its value is 0xff000003
print/x g_MAILBOX
continue

# Print g_MAILBOX as hex and verify its value is 0xff000005
print/x g_MAILBOX
continue

# Print g_MAILBOX as hex and verify its value is 0xff000000
print/x g_MAILBOX
continue

# Print g_MAILBOX as hex and verify its value is 0xff000004
print/x g_MAILBOX
continue

# Now, we entered endless loop, so use Ctrl+C to break execution
# Print g_MAILBOX as hex and verify its value is 0xffb12088
print/x g_MAILBOX

# If you reached here, test passed without errors :)
```

## Breakpoints

A breakpoint set with `break` uses a hardware watchpoint on the program counter. The core stops after the instruction at the breakpoint address has executed, so the effect of that instruction is already visible at a breakpoint stop. GDB shows the breakpoint address as `$pc` at the stop, and the first `stepi` from a breakpoint stop only moves `$pc` to the instruction that executes next.

## Conditional breakpoints

A breakpoint can have a condition. The sample app calls `decrement_mailbox` three times, with `g_MAILBOX` equal to 3, 2 and 1. To stop only in the last call, replace `break decrement_mailbox` in the script above with the line below, and keep only one of the three `continue` lines that follow `print g_MAILBOX`:

```
break decrement_mailbox if g_MAILBOX == 1
```

The core then stops in `decrement_mailbox` once, and `print g_MAILBOX` shows 1. `condition <N> <expression>` sets the condition of an existing breakpoint, and `condition <N>` removes it.

GDB evaluates the condition: the core stops at every hit of the breakpoint, GDB reads the values the condition needs and resumes the core if the condition is false. The GDB server does not evaluate conditions itself, so `set breakpoint condition-evaluation target` only prints a warning and GDB keeps evaluating them.
