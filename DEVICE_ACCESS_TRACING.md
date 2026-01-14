# Device Access Tracing

This document describes how to use the device access tracing feature to audit which tt-triage scripts are calling device register reads/writes, enabling verification of memory protection coverage.

## Purpose

The device access tracer captures full stack traces for all device register reads and writes performed by tt-exalens. This allows you to:

1. Identify which tt-triage scripts are accessing device registers
2. Map script functions to specific memory addresses
3. Verify that all device access is properly protected by memory access classes
4. Detect any unsafe direct reads/writes that bypass protection

## Quick Start

### 1. Enable Tracing

Set environment variables before running your tt-triage script:

```bash
export TTEXALENS_TRACE_DEVICE_ACCESS=1
export TTEXALENS_TRACE_OUTPUT=/tmp/device_access_trace.jsonl
```

### 2. Run Your tt-triage Script

```bash
python tt-triage/scripts/your_script.py
```

All device register operations will be logged to `/tmp/device_access_trace.jsonl`.

### 3. Analyze the Trace

```bash
python -m ttexalens.device_access_tracer --analyze /tmp/device_access_trace.jsonl
```

## Trace File Format

The trace file is in JSON Lines format (one JSON object per line):

```json
{
  "timestamp": 1768385998.750993,
  "timestamp_str": "2026-01-14 10:19:58",
  "operation": "read",
  "coord_x": 0,
  "coord_y": 0,
  "address": "0x1000",
  "size": 4,
  "stack_trace": [
    {
      "file": "/path/to/tt-triage/scripts/foo.py",
      "line": 42,
      "function": "bar",
      "code": "device.read_register(0, 0, 0x1000, 4)"
    },
    ...
  ]
}
```

### Fields

- **timestamp**: Unix timestamp (seconds since epoch)
- **timestamp_str**: Human-readable timestamp
- **operation**: "read" or "write"
- **coord_x**, **coord_y**: Device coordinates
- **address**: Memory address (hex string)
- **size**: Number of bytes read or written
- **stack_trace**: Full call stack (innermost frame first)
  - **file**: Source file path
  - **line**: Line number
  - **function**: Function name
  - **code**: Source code line

## Analysis Output

The analyzer provides two summaries:

### 1. Caller Summary

Shows which scripts/functions are accessing device registers:

```
File: /path/to/tt-triage/scripts/foo.py
Function: bar
  Reads:  10
  Writes: 5
  Unique addresses accessed: 8
```

### 2. Most Accessed Addresses

Shows the most frequently accessed memory addresses:

```
0x1000: 15 reads, 3 writes
0x2000: 8 reads, 12 writes
```

## Custom Analysis

You can parse the JSON Lines file yourself for custom analysis:

```python
import json

with open('/tmp/device_access_trace.jsonl', 'r') as f:
    for line in f:
        record = json.loads(line)

        # Find calls from specific script
        stack = record['stack_trace']
        for frame in stack:
            if 'my_script.py' in frame['file']:
                print(f"{record['operation']} @ {record['address']}")
```

## Verifying Memory Protection Coverage

### Workflow

1. **Run all tt-triage scripts** with tracing enabled
2. **Analyze the trace** to identify which scripts access device registers
3. **For each caller**:
   - Check if it uses `MemoryAccess` class (safe)
   - Check if it uses direct `UmdDevice` methods (potentially unsafe)
4. **Ensure all unsafe accesses** are wrapped in appropriate protection

### Example: Finding Unsafe Access

Look at the stack trace to see if calls go through memory protection:

**Safe path** (using MemoryAccess):
```
tt-triage/scripts/foo.py → MemoryAccess.read_word() → UmdDevice.__read_from_device_reg()
```

**Unsafe path** (direct access):
```
tt-triage/scripts/bar.py → UmdDevice.read_from_device() → UmdDevice.__read_from_device_reg()
```

## Performance Impact

- **When disabled** (default): Zero overhead
- **When enabled**: Moderate overhead due to stack trace capture
  - Use only for analysis runs, not production
  - Expect 10-50% slowdown depending on access frequency

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TTEXALENS_TRACE_DEVICE_ACCESS` | `0` | Set to `1` to enable tracing |
| `TTEXALENS_TRACE_OUTPUT` | `/tmp/device_access_trace.jsonl` | Output file path |

## Tips

### Running Multiple Scripts

Accumulate traces across multiple runs:

```bash
export TTEXALENS_TRACE_DEVICE_ACCESS=1
export TTEXALENS_TRACE_OUTPUT=/tmp/all_traces.jsonl

# Run all your scripts
for script in tt-triage/scripts/*.py; do
    python "$script"
done

# Analyze combined trace
python -m ttexalens.device_access_tracer --analyze /tmp/all_traces.jsonl
```

### Filtering by Address Range

```python
import json

# Find all accesses to a specific address range
with open('/tmp/device_access_trace.jsonl', 'r') as f:
    for line in f:
        record = json.loads(line)
        addr = int(record['address'], 16)
        if 0x1000 <= addr < 0x2000:
            print(f"{record['operation']} @ {record['address']} from {record['stack_trace'][-1]['file']}")
```

### Cleaning Up Between Runs

```bash
# Remove old trace before new run
rm /tmp/device_access_trace.jsonl
export TTEXALENS_TRACE_DEVICE_ACCESS=1
python your_script.py
```

## Troubleshooting

### No trace file generated

- Check that `TTEXALENS_TRACE_DEVICE_ACCESS=1` is set
- Check that the output directory exists and is writable
- Verify your script actually calls device register operations

### Trace file is huge

- This is expected for scripts with many device accesses
- The JSON Lines format is line-oriented, so you can process incrementally
- Consider filtering during analysis rather than storing everything

### Analysis shows no callers outside ttexalens

- The analyzer filters out ttexalens internal frames
- If you see no callers, your script might not be in the captured stack
- Check the raw JSON to see the full stack trace

## Implementation Details

The tracing is implemented using a decorator (`@trace_device_access`) applied to:

- `UmdDevice.__read_from_device_reg()`
- `UmdDevice.__write_to_device_reg()`

All device register operations funnel through these methods, ensuring complete coverage.
