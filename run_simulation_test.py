import unittest
import os

os.environ['TTEXALENS_TESTS_REMOTE'] = '1'

loader = unittest.TestLoader()
suite = loader.discover('test/ttexalens', pattern='*test*.py', top_level_dir='.')
filtered_suite = unittest.TestSuite()
for test_group in suite:
    for test_case in test_group:
        for test in test_case:
            # if 'test_minimal_run_generated_code (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_' in str(test):
            # if 'test_read_write_gpr (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_4_FW0)' in str(test):
            # if 'test_read_write_l1_memory (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)' in str(test):
            if 'test_read_write_private_memory (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)' in str(test):
            # if 'test_ebreak (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)' in str(test):
            # if 'test_ebreak_and_step (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)' in str(test):
            # if 'test_continue (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)' in str(test):
            # if 'test_halt_continue (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)' in str(test):
            # if 'test_halt_status (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)' in str(test):
            # if 'test_invalidate_cache (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)' in str(test):
            # if 'test_invalidate_cache_with_reset (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)' in str(test):
            # if 'test_invalidate_cache_with_nops_and_long_jump (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)' in str(test): # <-- Lasts too long to repro. Test is not needed for testing debugging hardware...
            # if 'test_watchpoint_on_pc_address (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)' in str(test):
            # if 'test_watchpoint_address (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)' in str(test):
            # if 'test_watchpoint_state (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)' in str(test):
            # if 'test_memory_watchpoint (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)' in str(test):
            # if 'test_bne_with_debug_fail (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)' in str(test):
            # if 'test_bne_without_debug (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)' in str(test):
            # if 'test_bne_with_debug_without_bp (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_1_FW0)' in str(test):
            # if 'test_ebreak (test.ttexalens.unit_tests.test_risc_debug.TestDebugging_2_FW0)' in str(test):
            # if 'test_write_read_bytes_buffer_08_ch0' in str(test):
                filtered_suite.addTest(test)
                print(f'Found {test}')

runner = unittest.TextTestRunner(verbosity=2)
runner.run(filtered_suite)
