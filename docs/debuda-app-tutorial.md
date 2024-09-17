# Debuda Application Tutorial

This tutorial shows houw to use the Debuda application.
It gives examples of basic commands, as well as how to run Debuda on remote machine and from cache.

To follow this tutorial, you should either [build Debuda from source](./../README.md#building-debuda) and run it through the python script with `./debuda.py`, or [install from wheel](./../README.md#building-and-installing-wheel) and run with `debuda.py`.

## Basic Usage

Running Debuda application should give the following output:

```bash
Verbosity level: 4
Output directory (output_dir) was not supplied and cannot be determined automatically. Continuing with limited functionality...
Device opened successfully.
Loading yaml file: '/tmp/debuda_server_WD5H5q/cluster_desc.yaml' (493 bytes loaded in 0.00s)
Opened device: id=0, arch=wormhole_b0, has_mmio=True, harvesting={'noc_translation': 'true', 'harvest_mask': 1}
gdb:None Current epoch:None(None) device:0 loc:18-18 >
```

The last line is the command prompt.
It shows the basic information, such as status of the gdb server, epoch of the running model, currently selected device id and targeted core location.
Some commands, such as `cdr`, use the currently-selected device and location to show information.
For example, running `cdr 18-18` will print a summary of the debug registers on core 18-18 of the current devcie.

Typing `h` or `help` into the prompt lists the available commands and gives a short explanation for each of them.
It is also possible to type `help <command-name>` to get more detailed help for each of available commands.

```
Full Name        Short    Description
---------------  -------  --------------------------------------------------------------------------------------------------------------------------------
exit             x        Exits the program. The optional argument represents the exit code. Defaults to 0.
help             h        Prints documentation summary. Use -v for details. If a command name is specified, it prints documentation for that command only.
reload           rl       Reloads files in debuda_commands directory. Useful for development of commands.
eval             ev       Evaluates a Python expression.
burst-read-xy    brxy     Reads and prints a block of data from address 'addr' at core <core-loc>.
core-debug-regs  cdr      Prints the state of the debug registers for core 'x-y'.
dump-gpr         gpr      Prints all RISC-V registers for BRISC, TRISC0, TRISC1, and TRISC2 on the current core.
pci-write-xy     wxy      Writes data word to address 'addr' at noc0 location x-y of the current chip.
riscv            rv       Commands for RISC-V debugging:
device           d        Shows a device summary. When no argument is supplied, it iterates through all devices used by the
gdb              gdb      Starts or stops gdb server.
go               go       Sets the current device/location.
run-elf          re       Loads an elf file into a brisc and runs it.
Use '-v' for more details.
```

More details about commands are available in [the documentation](./debuda-command-docs.md).

 
### Reading memory (`brxy`)

The `brxy` command can be used to read memory.
It is an acronym for burst read x-y, as it can also be used to sample memory during a time interval and produce a histogram of values.
The basic syntax of this command is:
```
brxy <core-loc> <addr> [ <word-count> ] [--sample <N>]
```

To read word from cache address 0x100 of core at 18-18 of the current device, you can use
```
brxy 18-18 0x100
```
which should produce an output akin to
```
18-18 (L1) :  0x00000100 (4 bytes)
0x00000100:  03020100
```
which specifies that four bytes read from L1 cache at address 0x100 are all 0.
We can also read multiple words, starting at some address, by specifying a number of after the address:
```
brxy 18-18 0x100 4
```
which gives
```
18-18 (L1) :  0x00000100 (16 bytes)
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
brxy 18-18 0x100 --sample 5
```
which gives an output
```
Sampling for 5.0 seconds...
18-18 (L1) :  0x00000100 (256) => 0x03020100 (50462976) - 924118 times
```
to be read as
```
core/dram loc : addres hex (address dec) => val hex (val dec) - # of occurences
```

For more advanced usecases of this command, refer to [the docummentation](./debuda-command-docs.md#brxy).


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
gdb:None Current epoch:None(None) device:0 loc:18-18 > brxy 18-18 0x100
18-18 (L1) : 0x00000100 (4 bytes)
0x00000100:  03020100
```
Now, let's write a new value:
```
gdb:None Current epoch:None(None) device:0 loc:18-18 > wxy 18-18 0x100 0x123
18-18 (L1) : 0x00000100 (256) <= 0x00000123 (291)
```
The output tells us that we have written to core 18-18 L1 memory, at address 0x100 (decimal 256), value 0x123, which is 291 in decimal:
```
core/dram loc : address hex (address dec) <= val hex (val dec)
```
If we now try to read this address, we get:
```
gdb:None Current epoch:None(None) device:0 loc:18-18 > brxy 18-18 0x100
18-18 (L1) : 0x00000100 (4 bytes)
0x00000100:  00000123
```
and we can affirm that the desired value has indeed been written.

Note that `wxy` can only write one word (4 bytes) at a time.

To see more details about this command, refer to [the documentation](./debuda-command-docs.md#wxy).


### Runing .elf files (`re`)

It is possible to run .elf files on Tenstorrent hardware through Debuda using `re` command.

We can try and run the sample program that is used in testing Debuda. 
First, be sure that you have [cloned Debuda repository and built Debuda](../README.md#building-debuda).
If everything worked as expected, there should be a file in `build/riscv-src/wormhole` directory named `run_elf_test.brisc.elf`.
That simple program writes value 0x12345678 to the address 0x0 in L1 memory of the selected core.
Currently, running `brxy 18-18 0x0` returns
```
18-18 (L1) : 0x00000000 (4 bytes)
0x00000000:  00000000
```
Let's try running our .elf file on that core:
```
re build/riscv-src/wormhole/run_elf_test.brisc.elf -l 18-18
```
The first argument is the path to the file we want to run, and the `-l` flag can be used to specify a single core to run the file on.
If not specified, the .elf program will be run on all available cores.
Let's check what's happened:
```
gdb:None Current epoch:None(None) device:0 loc:18-18 > brxy 18-18 0x0
18-18 (L1) : 0x00000000 (4 bytes)
0x00000000:  12345678
```
The pogram has executed and changed the value at 0x0.

To see more details about this command, see [documentation](./debuda-command-docs.md#re).


### Selecting active location and device (`go`)

Some commands act on the active device or location. It is possible to select a new device/location using the go command:
```
go -d 0
```
sets the devcie 0 to be active.

The `gpr` command is used to print RISC-V registers on the current core (for details, refer to [the docummentation](./debuda-command-docs.md#gpr)).
If we run it now, we will get:
```
gdb:None Current epoch:None(None) device:0 loc:18-18 > gpr
RISC-V registers for location 0,0 on device 0
Register     BRISC    TRISC0    TRISC1    TRISC2
-----------  -------  --------  --------  --------
...
```
To change the core location, we can use the `go` command:
```
go -l 20-20
```
and `gpr` will now give:
```
gdb:None Current epoch:None(None) device:0 loc:20-20 > gpr
RISC-V registers for location 2,2 on device 0
Register     BRISC    TRISC0    TRISC1    TRISC2
-----------  -------  --------  --------  --------
...
```
We can see that the core that `gpr` acts on has cganged.


## Using Debuda Server

Debuda can be started in client-server mode, which allows debugging on the remote machine.
The server can be started from within Buda runtime, or can be run as standalone program.
To start Debdua server, simply call
```
./debuda.py --server
```
You can optionally set the port to be used by specifying `--port=<port>`, but the default value of 5555 is fine for the purpose of this tutorial.
The server can be exited by simply pressing enter key in the terminal.

To attach to the server, you can spin up a Debuda client with
```
./debuda.py --remote --remote-address=<ip:port>
```
where you can specify the ip address and port, or write just
```
./debuda.py --remote --remote-address=<:port>
```
to connect to the port on the localhost.
Running
```
./debuda.py --remote
```
will try to connect to server on port 5555 running on localhost.
From there on, you can use Debuda the same way you would use it in local mode.


## Using Debuda's caching Mechanism

Debuda has a built-in caching mechanism which allows you to save the results of commands you run and reuse them later, or on a different machine.
The caching can be turned on using `--write-cache` flag in either local or client mode.
The cache is saved as a pickle file and can be read by running Debuda in cached mode.

Let's say that you need to save the results of some commands to take another look at them on another machine which does not have TT hardware.
You can run Debuda with cache writing turned on:
```
./debuda.py --write-cache --cache-path=tutorial_cache.pkl
```
By default, cache path is set to `debuda_cache.pkl`, but we have changed that here.
Let's write something to memory:
```
gdb:None Current epoch:None(None) device:0 loc:18-18 > wxy 18-18 0x100 0x1234
18-18 (L1) : 0x00000100 (256) <= 0x00001234 (4660)
```
and then read
```
gdb:None Current epoch:None(None) device:0 loc:18-18 > brxy 18-18 0x100 4
18-18 (L1) : 0x00000100 (16 bytes)
0x00000100:  00001234  00000000  00000000  00000000
```
Finally, by exiting Debuda, cache is automatically written to the specified file:
```
gdb:None Current epoch:None(None) device:0 loc:18-18 > x
Saving server cache to file tutorial_cache.pkl
  Saved 11 entries
```

We can now open this cache in Debuda by calling
```
./debuda.py --cached --cache-path=tutorial_cache.pkl
```
which gives
```
Verbosity level: 4
Starting Debuda from cache.
Loading server cache from file tutorial_cache.pkl
  Loaded 11 entries
Cache miss for get_runtime_data.
Loading yaml file: '/tmp/debuda_server_dQYfTS/cluster_desc.yaml' (493 bytes loaded in 0.00s)
Opened device: id=0, arch=wormhole_b0, has_mmio=True, harvesting={'noc_translation': 'true', 'harvest_mask': 1}
gdb:None Current epoch:None(None) device:0 loc:18-18 >
```

Since we are running from cache, we can't write to device:
```
gdb:None Current epoch:None(None) device:0 loc:18-18 > wxy 18-18 0x100 0x1234
--------------------------------------  -----------  --------------------------------------------------------------------------
debuda.py:428                           main_loop    new_navigation_suggestions = found_command["module"].run(
dbd/debuda_commands/pci-write-xy.py:52  run            tt_device.SERVER_IFC.pci_write32(
dbd/tt_debuda_ifc_cache.py:198          pci_write32      raise util.TTException("Device not available, cannot write to cache.")
dbd/tt_debuda_ifc_cache.py:198          pci_write32  TTException: Device not available, cannot write to cache.
--------------------------------------  -----------  --------------------------------------------------------------------------
```
but we can repeat our read command and get the same results:
```
gdb:None Current epoch:None(None) device:0 loc:18-18 > brxy 18-18 0x100 4
18-18 (L1) : 0x00000100 (16 bytes)
0x00000100:  00001234  00000000  00000000  00000000
```
Or we can even read a subset of addresses:
```
gdb:None Current epoch:None(None) device:0 loc:18-18 > brxy 18-18 0x104 2
18-18 (L1) : 0x00000104 (8 bytes)
0x00000104:  00000000  00000000
```
If we try to execute a command that wasn't cached, however, we get a cache miss error:
```
gdb:None Current epoch:None(None) device:0 loc:18-18 > brxy 18-18 0x200
Cache miss for pci_read32.
----------------------------------------  ----------------------  ---------------------------------------------------------------------------------
debuda.py:428                             main_loop               new_navigation_suggestions = found_command["module"].run(
dbd/debuda_commands/burst-read-xy.py:97   run                       print_a_pci_burst_read(
dbd/debuda_commands/burst-read-xy.py:123  print_a_pci_burst_read      data = read_words_from_device(core_loc, addr, device_id, word_count, context)
dbd/tt_debuda_lib.py:50                   read_words_from_device        word = context.server_ifc.pci_read32(
dbd/tt_debuda_ifc_cache.py:174            wrapper                         raise util.TTException(f"Cache miss for {func.__name__}.")
dbd/tt_debuda_ifc_cache.py:174            wrapper                 TTException: Cache miss for pci_read32.
----------------------------------------  ----------------------  ---------------------------------------------------------------------------------
```

For more details of inner workings of Debuda refer to [the `dbd` library tutorial](./debuda-lib-tutorial.md#debuda-internal-structure-and-initialization).


## Scripting and Development

### Simple scripting with --commands CLI argument

When starting Debuda, you can specify a list of commands to run. For example:
```
dbd/debuda.py --commands "go -l 20-20; gpr; x"
```
The above command will run `go -l 20-20`, changing active location to 20-20, followed by `gpr` and then exit. The output can then be redirected to a file for further processing.


### Developing new commands (`dbd/debuda_commands/` folder)

This folder contains python files that define Debuda commands. 
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
  - buda: needs output of a Buda run to interpret data from device,
  - metal: needs output of a Metal run to interpret data from device
- `common_option_names` (*list[str]*, optional): list of names of common options that command uses:
  - --verbosity: choose verbosity level; default: 4; available: 1-ERROR, 2-WARN, 3-DEBUG, 4-INFO, 5-VERBOSE,
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
    "context": ["limited", "buda", "metal"],
    "common_option_names": [ "--device", "--loc", "--verbosity" ],
    }
```

<div style="page-break-after: always;"></div>