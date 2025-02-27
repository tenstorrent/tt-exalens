## Architecture

Each tenstorrent chip has many tensix cores. Each tensix core has couple of riscv cores that can be debugged. Since each riscv core has its own private memory and code that is being executed, gdb server exposes every riscv core as a separate process that can be debugged.

TTExaLens application is hosting gdb server. You should use gdb client to connect to gdb server and you need to enable multiprocess debugging to be able to debug multiple cores at the same time.

## Starting gdb server

You can start gdb server with ttlens application:

- With command line argument: Start ttlens with `--start-gdb=<gdb_port>` where `<gdb_port>` is integer number for port that will be used for gdb server.
- With `gdb` command: After you start TT-ExaLens, you can use `gdb` command to start gdb server. Run `gdb start --port <port>` where `<port>` is integer number fo port that will be used for gdb server.

After starting gdb server, you can stop it with `gdb` command. Run `gdb stop`.

## Connecting gdb client

- Start gdb client (`./sfpi/compiler/bin/riscv32-unknown-elf-gdb` in TT-ExaLens repository).
***Note:*** Currently gdb client is not part of sfpi library.
You will need to clone it from https://github.com/tenstorrent-metal/sfpi-rel.
- If you want to debug client/server communication execute `set debug remote 1` in GDB client
- Connect GDB client to TT-ExaLens: `target extended-remote localhost:<gdb_port>` where `<gdb_port>` is port used in TT-ExaLens when starting gdb server.

After connection has been established, you can use `info os processes` to list all available processes that you can debug with GDB. Use `attach <pid>` to start debugging selested riscv core.

## Sample app debugging script:

Once you started gdb server, you can use run-elf command to execute `ttlens/riscv-src/sample.cc` application on chip. For wormhole, you can execute `re build/riscv-src/wormhole/sample.brisc.elf` to run application on brisc core.

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
