# Debug Tools — Example Scenarios

Example usage scenarios for three Tenstorrent debug tools: **tt-exalens**, **tt-triage**,
and **dprint**. Each section is framed as a realistic debugging workflow so it's clear when
and why you'd reach for each tool.

## How they fit together

- **dprint** — instrument *your own kernel code* ahead of time to emit values from inside the kernel.
- **tt-exalens** — *interactively* inspect any address, register, or call stack on a live device, with no code changes needed.
- **tt-triage** — *automatically* sweep the whole device and tell you which area is broken, so you know where to point tt-exalens.

A typical flow: triage flags a bad subsystem → tt-exalens inspects the cores/memory there →
if it's your kernel logic, add dprint and re-run.

---

## 1. tt-exalens — low-level hardware debugger

The general-purpose debugger for direct access to Wormhole/Blackhole devices. Runs as an
interactive REPL, in command mode for scripting, as a GDB server, or via the `ttexalens`
Python library.

### Scenario A: "A kernel hangs and I want to see where each RISC-V core is stuck"

Launch interactively and pull call stacks off the cores using the ELF:

```bash
tt-exalens
> device                       # summary of all cores / device state
> callstack build/riscv-src/wormhole/sample.brisc.elf -r brisc
> dump-gpr                      # dump BRISC/TRISC0-2 registers
```

Use this when an op never completes — the call stack tells you whether the core is spinning
in a wait loop, faulted, or stuck in a specific function.

### Scenario B: "I suspect a value in L1/dram is wrong"

Read memory directly at a NOC location and watch it change over time:

```bash
tt-exalens --commands="brxy 1,1 0x0 16; brxy 1,1 0x0 32 --format i8 --sample 5"
```

The `--sample 5` form polls the same address for 5 seconds — handy for catching a value that
should be updating (or shouldn't be) while a kernel runs.

### Scenario C: "I want source-level stepping in GDB"

Bring up the GDB stub and attach a standard RISC-V GDB:

```bash
tt-exalens --gdb
# or from inside the REPL:
> gdb start --port 6767
```

### Scenario D: scripted / CI check via the Python API

```python
from ttexalens import tt_exalens_init, read_words_from_device
tt_exalens_init.init_ttexalens()
status = read_words_from_device("1,1", 0x0, word_count=1)[0]
assert status == 0xDEADBEEF, f"unexpected handshake value {status:#x}"
```

Use this to bake hardware-state assertions into automated tests.

---

## 2. tt-triage — automated device-state diagnosis

A higher-level "what's wrong with this board right now?" tool. It scripts tt-exalens APIs to
sweep device state and flag anomalies, rather than you poking addresses by hand. (It lives
alongside tt-metal and builds on tt-exalens; tt-exalens provides the device-access-tracing
support it uses for audits.)

### Scenario A: "The board is misbehaving — run a full triage sweep"

```bash
python tt-triage/scripts/triage.py
```

You'd run this first when something is broken but you don't yet know *what* — it checks core
states, NOC health, memory regions, and reports which subsystems look bad, pointing you at
where to dig in with tt-exalens.

### Scenario B: "Audit which device memory a script touched" (memory-protection audit)

Enable device-access tracing so triage can verify a script only touched memory it was
allowed to:

```bash
export TTEXALENS_TRACE_DEVICE_ACCESS=1
export TTEXALENS_TRACE_OUTPUT=/tmp/trace.jsonl
python tt-triage/scripts/your_script.py
# then inspect /tmp/trace.jsonl for out-of-bounds accesses
```

(See [DEVICE_ACCESS_TRACING.md](../DEVICE_ACCESS_TRACING.md) for the tracing format.)

### Scenario C: post-failure capture in CI

Run triage automatically when a test job fails, archiving the diagnosis so you can debug a
hang that you can't reproduce locally.

> Note: tt-triage's exact script names/flags live in the tt-metal repo. The workflow above is
> described from how this repo integrates with it — confirm the precise entry points there if
> you want exact command strings.

---

## 3. dprint — kernel debug printing

A compile-time-validated `printf` for RISC-V kernel code. You add `DPRINT(...)` calls in C++
kernel source; format strings and argument types are checked at compile time, and output is
serialized to a per-core memory buffer that you read back from the host.

### Scenario A: "Is my loop counter what I think it is?"

In the kernel (`riscv-src/dprint.cc`):

```cpp
DPRINT("n = {}\n", n);
```

Then read the dprint buffer from the host side to see the emitted values — the classic "add a
print to see what's happening" loop, but on-device.

### Scenario B: reordering / reusing arguments with indexed placeholders

```cpp
DPRINT("Simple: n = {0}\n", n);
DPRINT("Repeat: n = {0}, n = {0}\n", n);     // print the same arg twice
DPRINT("Order: {1}, {0}\n", n, 5);           // out-of-order
DPRINT("Test: n = {0}, i = {1}, n = {0}\n", n, 5);
```

Useful for laying out readable log lines without repeating computations.

### Scenario C: tracing recursion / control flow

```cpp
void recurse(int n) {
    DPRINT("enter recurse n = {}\n", n);
    if (n > 0) recurse(n - 1);
}
```

Confirms a recursive or branchy kernel path actually executes the way you expect, with one
print per entry.

The key win over `tt-exalens brxy`-style poking: the type-to-format-specifier mapping
(`int`→`d`, `float`→`f`, `const char*`→`s`, etc.) and placeholder-count validation happen at
**compile time**, so a malformed print fails the build instead of producing garbage at runtime.
