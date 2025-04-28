import unittest
import os
import sys
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description='Run RISC debug tests')
parser.add_argument('--id', type=int, help='Run test by ID (1-based index)')
parser.add_argument('--name', type=str, help='Run test by name (substring match)')
parser.add_argument('--list', action='store_true', help='List all available tests')
parser.add_argument('--enable', type=str, nargs='+', help='Enable specific tests by ID or name patterns (space separated)')
parser.add_argument('--disable', type=str, nargs='+', help='Disable specific tests by ID or name patterns (space separated)')
parser.add_argument('--run-all', action='store_true', help='Run all tests (default)')
args = parser.parse_args()

os.environ['TTEXALENS_TESTS_REMOTE'] = '1'

# List of test names to include in the test suite
test_names = [
    'test_minimal_run_generated_code (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_',
    'test_read_write_gpr (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_4_FW0)',
    'test_read_write_l1_memory (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)',
    'test_read_write_private_memory (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)',
    'test_ebreak (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)',
    'test_ebreak_and_step (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)',
    'test_continue (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)',
    'test_halt_continue (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)',
    'test_halt_status (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)',
    'test_invalidate_cache (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)',
    'test_invalidate_cache_with_reset (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)',
    # 'test_invalidate_cache_with_nops_and_long_jump (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)', # <-- Lasts too long to repro. Test is not needed for testing debugging hardware...
    'test_watchpoint_on_pc_address (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)',
    'test_watchpoint_address (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)',
    'test_watchpoint_state (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)',
    'test_memory_watchpoint (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)',
    'test_bne_with_debug_fail (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)',
    'test_bne_without_debug (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)',
    'test_bne_with_debug_without_bp (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)',
    'test_ebreak (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_2_FW0)',
    'test_write_read_bytes_buffer_08_ch0'
]

# Just list the tests if --list is specified
if args.list:
    print("Available tests:")
    for i, test_name in enumerate(test_names, 1):
        print(f"{i}. {test_name}")
    sys.exit(0)

# Initialize all tests as enabled by default (if --enable is not specified)
enabled_tests = {name: True for name in test_names}

# Helper function to check if a test matches an ID or pattern
def test_matches(test_name, pattern):
    try:
        # Check if pattern is a valid integer (ID)
        test_id = int(pattern)
        # Convert to 1-based index
        return test_id == test_names.index(test_name) + 1
    except ValueError:
        # Pattern is a string
        return pattern.lower() in test_name.lower()

# Process enable/disable arguments
if args.enable:
    # If --enable is specified, first disable all tests
    enabled_tests = {name: False for name in test_names}
    # Then enable only the specified tests
    for pattern in args.enable:
        for test_name in test_names:
            if test_matches(test_name, pattern):
                enabled_tests[test_name] = True
                
if args.disable:
    # Disable specified tests
    for pattern in args.disable:
        for test_name in test_names:
            if test_matches(test_name, pattern):
                enabled_tests[test_name] = False

# Process specific test selection (--id or --name)
if args.id is not None:
    # Override enable/disable with specific ID selection
    enabled_tests = {name: False for name in test_names}
    if 1 <= args.id <= len(test_names):
        enabled_tests[test_names[args.id - 1]] = True
    else:
        print(f"Error: Test ID must be between 1 and {len(test_names)}")
        sys.exit(1)
elif args.name is not None:
    # Override enable/disable with specific name selection
    enabled_tests = {name: False for name in test_names}
    for test_name in test_names:
        if args.name.lower() in test_name.lower():
            enabled_tests[test_name] = True
    
    if not any(enabled_tests.values()):
        print(f"Error: No tests found matching '{args.name}'")
        sys.exit(1)

# Filter to only enabled tests
active_test_names = [name for name, enabled in enabled_tests.items() if enabled]

# Print tests that will be run
print("Tests that will be run:")
for i, test_name in enumerate(active_test_names, 1):
    print(f"{i}. {test_name}")

# Load and filter tests
loader = unittest.TestLoader()
suite = loader.discover('test/ttexalens', pattern='*test*.py', top_level_dir='.')
filtered_suite = unittest.TestSuite()

for test_group in suite:
    for test_case in test_group:
        for test in test_case:
            test_str = str(test)
            # Add test if it matches any name in our active list
            for test_name in active_test_names:
                if test_name in test_str:
                    filtered_suite.addTest(test)
                    print(f'Found {test}')
                    break  # No need to check other test names

# Run the filtered tests
runner = unittest.TextTestRunner(verbosity=2)
runner.run(filtered_suite)
