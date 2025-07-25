# Command-Line Application Tutorial

This tutorial explains how to use the ttexalens command-line application.
It includes examples of basic commands, remote usage, and running from cache.

To follow this tutorial, you can either:

- [Build from source](./../README.md#building-the-library-and-the-application) and run the script with `./tt-exalens.py`, or
- [Install from wheel](./../README.md#building-and-installing-wheel) and run it using the `tt-exalens` command.

## Basic Usage

To start the application, run:

```bash
./tt-exalens.py
```

If installed via wheel, you can also run:
```bash
ttexalens
```

Running the application should produce the following prompt:

```bash
gdb:None device:0 loc:1-1 (0, 0) >
```

This is the command prompt. It displays key information such as:
- GDB server status (gdb:None)
- Currently selected device ID (device:0)
- Targeted core location (loc:1-1 (0, 0))

Some commands (like ```re```) use the currently selected device and location if no parameters are provided.

For example, running:
```
re build/riscv-src/wormhole/run_elf_test.brisc.elf
```
will load the ELF file onto the currently selected core and device (initially, core (0, 0) of device 0).

Typing `h` or `help` at the prompt to list available commands with brief descriptions.

For detailed help on a specific command, use:
```
help <command-name>
```

```
Full Name        Short    Description
---------------  -------  --------------------------------------------------------------------------------------------------------------------------------
exit             x        Exits the program. The optional argument represents the exit code. Defaults to 0.
help             h        Prints documentation summary. Use -v for details. If a command name is specified, it prints documentation for that command only.
reload           rl       Reloads files in cli_commands directory. Useful for development of commands.
burst-read-xy    brxy     Reads and prints a block of data from address 'addr' at core <core-loc>.
dump-gpr         gpr      Prints all RISC-V registers for BRISC, TRISC0, TRISC1, and TRISC2 on the current core.
write-xy         wxy      Writes data word to address 'addr' at noc0 location x-y of the current chip.
riscv            rv       Commands for RISC-V debugging:
device           d        Shows a device summary. When no argument is supplied, it iterates through all devices
gdb              gdb      Starts or stops gdb server.
go               go       Sets the current device/location.
run-elf          re       Loads an elf file into a brisc and runs it.
Use '-v' for more details.
```

More details about commands are available in [the documentation](./ttexalens-app-docs.md).


### Reading memory (`brxy`)

The `brxy` command can be used to read memory.
It is an acronym for burst read x-y, as it can also be used to sample memory during a time interval and produce a histogram of values.
The basic syntax of this command is:
```
brxy <core-loc> <addr> [ <word-count> ] [--sample <N>]
```

To read word from cache address 0x100 of core at 0,0 of the current device, you can use
```
brxy 0,0 0x100
```
which should produce an output akin to
```
0,0 (L1) :  0x00000100 (4 bytes)
0x00000100:  03020100
```
which specifies that four bytes read from L1 cache at address 0x100 are all 0.
We can also read multiple words, starting at some address, by specifying a number of after the address:
```
brxy 0,0 0x100 4
```
which gives
```
0,0 (L1) :  0x00000100 (16 bytes)
0x00000100:  03020100  00000000  00000000  00000000
```
Now sixteen bytes are read, starting at address 0x100, and they are all 0.

It is also possible to read from a DRAM channel in a simillar way:
```
brxy ch3 0x100
```
which gives
```
ch3 (DRAM) : 0x00000100 (4 bytes)
0x00000100:  55555555
```

It is also possible to sample the value of a memory address for a number of seconds:
```
brxy 0,0 0x100 --sample 5
```
which gives an output
```
Sampling for 5.0 seconds...
0,0 (L1) :  0x00000100 (256) => 0x03020100 (50462976) - 924118 times
```
to be read as
```
core/dram loc : addres hex (address dec) => val hex (val dec) - # of occurences
```

For more advanced usecases of this command, refer to [the docummentation](./ttexalens-app-docs.md#brxy).


### Writing to memory (`wxy`)

The `brxy` command has given us gibberish results, as it read memory that hasn't yet been written to.
It is possible to acces memory and write directly to it using the `wxy` command (*write x-y*).
The syntax is similar to `brxy`:
```
wxy <core-loc> <addr> <data>
```

Let's try out this command.
First, let's check the value written on address 0x100:
```
gdb:None Current epoch:None(None) device:0 loc:1-1 (0,0) > brxy 0,0 0x100
0,0 (L1) : 0x00000100 (4 bytes)
0x00000100:  03020100
```
Now, let's write a new value:
```
gdb:None Current epoch:None(None) device:0 loc:1-1 (0,0) > wxy 0,0 0x100 0x123
0,0 (L1) : 0x00000100 (256) <= 0x00000123 (291)
```
The output tells us that we have written to core 0,0 L1 memory, at address 0x100 (decimal 256), value 0x123, which is 291 in decimal:
```
core/dram loc : address hex (address dec) <= val hex (val dec)
```
If we now try to read this address, we get:
```
gdb:None Current epoch:None(None) device:0 loc:1-1 (0,0) > brxy 0,0 0x100
0,0 (L1) : 0x00000100 (4 bytes)
0x00000100:  00000123
```
and we can affirm that the desired value has indeed been written.

Note that `wxy` can only write one word (4 bytes) at a time.

To see more details about this command, refer to [the documentation](./ttexalens-app-docs.md#wxy).


### Runing .elf files (`re`)

It is possible to run .elf files on Tenstorrent hardware through TTExaLens using `re` command.

We can try and run the sample program that is used in testing TTExaLens.
First, be sure that you have [cloned TTExaLens repository and built TTExaLens](../README.md#building-ttexalens).
If everything worked as expected, there should be a file in `build/riscv-src/wormhole` directory named `run_elf_test.brisc.elf`.
That simple program writes value 0x12345678 to the address 0x0 in L1 memory of the selected core.
Currently, running `brxy 0,0 0x0` returns
```
0,0 (L1) : 0x00000000 (4 bytes)
0x00000000:  00000000
```
Let's try running our .elf file on that core:
```
re build/riscv-src/wormhole/run_elf_test.brisc.elf -l 0,0
```
The first argument is the path to the file we want to run, and the `-l` flag can be used to specify a single core to run the file on.
If not specified, the .elf program will be run on all available cores.
Let's check what's happened:
```
gdb:None Current epoch:None(None) device:0 loc:1-1 (0,0) > brxy 0,0 0x0
0,0 (L1) : 0x00000000 (4 bytes)
0x00000000:  12345678
```
The pogram has executed and changed the value at 0x0.

To see more details about this command, see [documentation](./ttexalens-app-docs.md#re).


### Selecting active location and device (`go`)

Some commands act on the active device or location. It is possible to select a new device/location using the go command:
```
go -d 0
```
sets the devcie 0 to be active.

The `gpr` command is used to print RISC-V registers on the current core (for details, refer to [the docummentation](./ttexalens-app-docs.md#gpr)).
If we run it now, we will get:
```
gdb:None Current epoch:None(None) device:0 loc:1-1 (0,0) > gpr
RISC-V registers for location 0,0 on device 0
Register     BRISC    TRISC0    TRISC1    TRISC2
-----------  -------  --------  --------  --------
...
```
To change the core location, we can use the `go` command:
```
go -l 2,2
```
and `gpr` will now give:
```
gdb:None Current epoch:None(None) device:0 loc:3-3 (2,2) > gpr
RISC-V registers for location 2,2 on device 0
Register     BRISC    TRISC0    TRISC1    TRISC2
-----------  -------  --------  --------  --------
...
```
We can see that the core that `gpr` acts on has changed.


## Using the Server

The debugger can be started in client-server mode, enabling remote debugging.

To start the server as a standalone program, simply run:
```
./tt-exalens.py --server
```
You can optionally set the port to be used by specifying `--port=<port>`, but the default value of 5555 is fine for the purpose of this tutorial.
The server can be exited by simply pressing enter key in the terminal.

To attach to the server, start the client with:
```
./tt-exalens.py --remote --remote-address=<ip:port>
```
where you can specify the ip address and port, or write just
```
./tt-exalens.py --remote --remote-address=<:port>
```
to connect to the port on the localhost.
Running
```
./tt-exalens.py --remote
```
will try to connect to server on port 5555 running on localhost.
From there on, you can use TTExaLens the same way you would use it in local mode.


## Using the Caching Mechanism

The debugger includes a built-in caching mechanism that allows you to save the results of executed commands and reuse them later, even on a different machine.

Caching can be enabled using the `--write-cache` flag in both local and client modes.
The results are saved as a `.pkl` (pickle) file, which can later be used in cached mode.

For example, to save results for later inspection on a machine without Tenstorrent hardware, run:

```
./tt-exalens.py --write-cache --cache-path=tutorial_cache.pkl
```
By default, cache path is set to `ttexalens_cache.pkl`, but we have changed that here.
Let's write something to memory:
```
gdb:None Current epoch:None(None) device:0 loc:1-1 (0,0) > wxy 0,0 0x100 0x1234
0,0 (L1) : 0x00000100 (256) <= 0x00001234 (4660)
```
and then read
```
gdb:None Current epoch:None(None) device:0 loc:1-1 (0,0) > brxy 0,0 0x100 4
0,0 (L1) : 0x00000100 (16 bytes)
0x00000100:  00001234  00000000  00000000  00000000
```
Finally, the cache is automatically written to the specified file upon exit:
```
gdb:None Current epoch:None(None) device:0 loc:1-1 (0,0) > x
Saving server cache to file tutorial_cache.pkl
  Saved 11 entries
```

We can now open this cache by running:
```
./tt-exalens.py --cached --cache-path=tutorial_cache.pkl
```
This will produce output like:
```
Starting TTExaLens from cache.
Loading server cache from file tutorial_cache.pkl
  Loaded 7 entries
gdb:None device:0 loc:1-1 (0, 0) >
```

Since we are running from cache, we can't write to device:
```
gdb:None Current epoch:None(None) device:0 loc:1-1 (0,0) > wxy 0,0 0x100 0x1234
------------------------------------------  -----------  --------------------------------------------------------------------------
tt-exalens:428                              main_loop    new_navigation_suggestions = found_command["module"].run(
ttexalens/cli_commands/pci-write-xy.py:52   run            device.SERVER_IFC.pci_write32(
ttexalens/tt_exalens_ifc_cache.py:198       pci_write32      raise util.TTException("Device not available, cannot write to cache.")
ttexalens/tt_exalens_ifc_cache.py:198       pci_write32  TTException: Device not available, cannot write to cache.
------------------------------------------  -----------  --------------------------------------------------------------------------
```
but we can repeat our read command and get the same results:
```
gdb:None Current epoch:None(None) device:0 loc:1-1 (0,0) > brxy 0,0 0x100 4
0,0 (L1) : 0x00000100 (16 bytes)
0x00000100:  00001234  00000000  00000000  00000000
```
Or we can even read a subset of addresses:
```
gdb:None Current epoch:None(None) device:0 loc:1-1 (0,0) > brxy 0,0 0x104 2
0,0 (L1) : 0x00000104 (8 bytes)
0x00000104:  00000000  00000000
```
If we try to execute a command that wasn't cached, however, we get a cache miss error:
```
gdb:None Current epoch:None(None) device:0 loc:1-1(0,0) > brxy 0,0 0x200
Cache miss for pci_read32.
--------------------------------------------  ----------------------  ---------------------------------------------------------------------------------
cli.py:428                                    main_loop               new_navigation_suggestions = found_command["module"].run(
ttexalens/cli_commands/burst-read-xy.py:97    run                       print_a_pci_burst_read(
ttexalens/cli_commands/burst-read-xy.py:123   print_a_pci_burst_read      data = read_words_from_device(core_loc, addr, device_id, word_count, context)
ttexalens/tt_exalens_lib.py:50                      read_words_from_device        word = context.server_ifc.pci_read32(
ttexalens/tt_exalens_ifc_cache.py:174               wrapper                         raise util.TTException(f"Cache miss for {func.__name__}.")
ttexalens/tt_exalens_ifc_cache.py:174               wrapper                 TTException: Cache miss for pci_read32.
--------------------------------------------  ----------------------  ---------------------------------------------------------------------------------
```

For more details refer to  [the `ttexalens` library tutorial](./ttexalens-lib-tutorial.md#ttexalens-internal-structure-and-initialization).


## Scripting and Development

### Simple scripting with --commands CLI argument

When starting the application, you can specify a list of commands to run. For example:
```
tt-exalens --commands "go -l 2,2; gpr; x"
```
This will:
- Set the active location to (2,2) using go -l 2,2
- Run gpr to print general-purpose registers
- Exit the application with x

The output can be redirected to a file for further processing:
```
tt-exalens --commands "go -l 2,2; gpr; x" > output.txt
```

### Developing new commands (`ttexalens/cli_commands/` folder)

This folder contains python files that define TTExaLens commands.
To create a new command, create a new file in this folder.
The file name will be the command name. For example, `op-map.py` defines the `op-map` command.
The file must contain a function called `run()` which represents the main entry point for the command.
The command_metadata dictionary must also be defined.
The fields of this dictionary are as follwos:
- `short` (*str*, optional): short name of the command
- `long` (*str*, optional): long name of the command
- `type` (*str*): type of the command:
  - dev (*under development*),
  - high-level,
  - low-level
- `description` (*str*): command description, usually `__doc__` variable used to utilize module docstring
- `context` (*list[str]*): which context has access to this command:
  - limited: needs no output, works with raw data from device,
  - metal: needs output of a Metal run to interpret data from device
- `common_option_names` (*list[str]*, optional): list of names of common options that command uses:
  - --verbose, -v: Execute command with verbose output, default: false
  - --test: run in test mode; default: false,
  - --device: device ID to run the command on; default: current device,
  - --loc: grid location for running the command; default: current location,
  - --risc: RiscV ID (0: brisc, 1-3 trisc, all); default: all


Note: long and short name can't be left out.


For example:

```
command_metadata = {
    "short": "examplecmd",
    "type": "low-level",
    "description": "This is a description of the command.",
    "context": ["limited", "metal"],
    "common_option_names": [ "--device", "--loc", "--verbose", "--risc" ],
    }
```

<div style="page-break-after: always;"></div>
