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

# Start the GDB server in the background
#./tt-exalens.py --start-gdb=$PORT

# # Wait until port is open
# echo "Waiting for GDB server on port $PORT..."
# while ! nc -z localhost "$PORT"; do
#     sleep 0.2
# done
# echo "GDB server ready."

# Generate a temporary GDB script
GDB_SCRIPT=$(mktemp /tmp/gdbscript.XXXX.gdb)

cat > "$GDB_SCRIPT" <<EOF
set pagination off
set confirm off
set logging file gdb.output

target extended-remote localhost:$PORT
attach $PID
add-symbol-file $ELF $OFFSET
set logging enabled on
bt
set logging enabled off
detach
q
EOF

# Run GDB with the generated script
./build/sfpi/compiler/bin/riscv32-tt-elf-gdb -x "$GDB_SCRIPT"

# Clean up
rm "$GDB_SCRIPT"
