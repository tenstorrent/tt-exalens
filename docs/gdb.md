## Architecture

Each tenstorrent chip has many tensix cores. Each tensix core has couple of riscv cores that can be debugged. Since each riscv core has its own private memory and code that is being executed, gdb server exposes every riscv core as a separate process that can be debugged.

Debuda application is hosting gdb server. You should use gdb client to connect to gdb server and you need to enable multiprocess debugging to be able to debug multiple cores at the same time.

## Starting gdb server

You can start gdb server with debuda application:

- With command line argument: Start debuda with `--start-gdb=<gdb_port>` where `<gdb_port>` is integer number for port that will be used for gdb server.
- With `gdb` command: After you start debuda, you can use `gdb` command to start gdb server. Run `gdb start --port <port>` where `<port>` is integer number fo port that will be used for gdb server.

After starting gdb server, you can stop it with `gdb` command. Run `gdb stop`.

## Connecting gdb client

- Start gdb client (`./third_party/sfpi/compiler/bin/riscv32-unknown-elf-gdb` in debuda repository).
- If you want to debug client/server communication execute `set debug remote 1` in GDB client
- Connect GDB client to debuda: `target extended-remote localhost:6767`

After connection has been established, you can use `info os processes` to list all available processes that you can debug with GDB. Use `attach <pid>` to start debugging selested riscv core.
