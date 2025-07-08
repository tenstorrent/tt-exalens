#!/bin/bash

# Check if all required arguments are passed
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <port> <pid> <path-to-elf> <offset>"
    exit 1
fi

PORT=$1
PID=$2
ELF=$3
OFFSET=$4

[ -p mypipe ] || mkfifo mypipe
tail -f mypipe | ./tt-exalens.py --start-gdb=$PORT > exalens_log.txt &

sleep 1 # Wait for the GDB server to start

# Generate a temporary GDB script
GDB_SCRIPT=$(mktemp /tmp/gdbscript.XXXX.gdb)

cat > "$GDB_SCRIPT" <<EOF
# Make script run without user interaction
set pagination off
set confirm off

# Logging for callstack results
set logging file callstack.output
# Clear previous output
shell > callstack.output

# Connect to the GDB server
target extended-remote localhost:$PORT

# Attach to the process
python
try:
    gdb.execute("attach $PID")
except gdb.error as e:
    if "failed" in str(e):
        print("Failed to attach to process. Aborting...\nTry resseting the board with tt-smi.")
    else:
        print(e)
end

# Add elf file
python
try:
    gdb.execute("add-symbol-file $ELF $OFFSET")
except gdb.error as e:
    print(e)
end

# Get callstack and log it
set logging enabled on
backtrace
set logging enabled off

# Detach from the process
python
try:
    gdb.execute("detach")
except gdb.error as e:
    print("Detach failed:", e)
end

# Exit GDB
quit
EOF

# Run GDB with the generated script
./build/sfpi/compiler/bin/riscv32-tt-elf-gdb -q -batch -x "$GDB_SCRIPT" > tmp.txt

# Close port
sudo kill -9 $(sudo lsof -t -i :$PORT)

# Clean up
rm "$GDB_SCRIPT"
