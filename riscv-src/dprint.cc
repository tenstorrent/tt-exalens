// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

#include "dprint.hpp"

void halt() {
    // Halt core with ebrake instruction
    asm volatile("ebreak");
}

void recurse(int n) {
    DPRINT("n = {}\n", n);
    if (n > 0) {
        recurse(n - 1);
    }
}

void some_function(int n) {
    DPRINT("Entering some_function with n = {}\n", n);
    recurse(n);
    DPRINT("n = {}\n", n);
    DPRINT("Exiting some_function with n = {}\n", n);
}

void test_indexed_placeholders(int n) {
    // Test 1: Simple indexed format
    DPRINT("Simple: n = {0}\n", n);

    // Test 2: Repeated index
    DPRINT("Repeat: n = {0}, n = {0}\n", n);

    // Test 3: Multiple arguments with indices
    DPRINT("Test3: n = {0}, i = {1}, n = {0}\n", n, 5);

    // Test 4: Out of order indices
    DPRINT("Order: {1}, {0}\n", n, 5);
}

void dprint_message_size_tests() {
    // Compile-time tests for calculate_dprint_message_size
    static_assert(dprint_detail::calculate_dprint_message_size<int>() == 4, "int should be 4 bytes");
    static_assert(dprint_detail::calculate_dprint_message_size<char>() == 1, "char should be 1 byte");
    static_assert(dprint_detail::calculate_dprint_message_size<char*>() == 4, "char* should be 4 bytes");
    static_assert(dprint_detail::calculate_dprint_message_size<const char*>() == 4, "const char* should be 4 bytes");
    static_assert(dprint_detail::calculate_dprint_message_size<int, const char*>() == 8,
                  "int + const char* should be 8 bytes");
    static_assert(dprint_detail::calculate_dprint_message_size<int, const char*, double>() == 16,
                  "int + const char* + double should be 16 bytes");

    // Test the wrapper function at compile time
    constexpr auto size1 = dprint_detail::calculate_dprint_message_size_from_args(42);
    static_assert(size1 == 4 + dprint_detail::message_header_size, "single int argument should be 4 bytes");

    constexpr auto size2 = dprint_detail::calculate_dprint_message_size_from_args("hello");
    static_assert(size2 == 4 + dprint_detail::message_header_size, "single const char* argument should be 4 bytes");

    constexpr auto size3 = dprint_detail::calculate_dprint_message_size_from_args(42, "hello");
    static_assert(size3 == 8 + dprint_detail::message_header_size, "int + const char* should be 8 bytes");
}

void dprint_format_validation_tests() {
    // Test compile-time validation of type mapping and basic functionality

    // Test that basic type character mapping works at compile time
    static_assert(dprint_detail::get_type_char<int>() == 'd', "int maps to 'd'");
    static_assert(dprint_detail::get_type_char<unsigned int>() == 'u', "unsigned int maps to 'u'");
    static_assert(dprint_detail::get_type_char<float>() == 'f', "float maps to 'f'");
    static_assert(dprint_detail::get_type_char<char>() == 'c', "char maps to 'c'");
    static_assert(dprint_detail::get_type_char<const char*>() == 's', "const char* maps to 's'");
    static_assert(dprint_detail::get_type_char<char*>() == 's', "char* maps to 's'");
    static_assert(dprint_detail::get_type_char<bool>() == 'd', "bool maps to 'd'");

    // Test placeholder counting functionality on literal strings
    static_assert(dprint_detail::count_placeholders("Value: {}\n") == 1, "Should find exactly 1 placeholder");
    static_assert(dprint_detail::count_placeholders("Values: {} and {}\n") == 2, "Should find exactly 2 placeholders");
    static_assert(dprint_detail::count_placeholders("No placeholders here\n") == 0, "Should find no placeholders");
    static_assert(dprint_detail::count_placeholders("Start {} middle {} end {}\n") == 3,
                  "Should find exactly 3 placeholders");

    // Runtime test of the actual function (demonstrates core functionality)
    constexpr char test_format[] = "Test: {} and {}\n";
    constexpr auto result = dprint_detail::update_format_string<sizeof(test_format), int, const char*>(test_format);
    static_assert(result.check("Test: {0:d} and {1:s}\n"), "Resulting format string should match expected output");
}

void demonstrate_format_string_usage() {
    // Examples of how to use the update_format_string function with validation

    // Example 1: Valid usage - arguments match placeholders
    constexpr char format1[] = "Processing item {} with status {}\n";
    constexpr auto updated1 = dprint_detail::update_format_string<sizeof(format1), int, const char*>(format1);
    static_assert(updated1.check("Processing item {0:d} with status {1:s}\n"),
                  "Updated format string should match expected output");

    // Example 2: Original user requirement with verification
    constexpr char format2[] = "Some number {}, and some text {}\n";
    constexpr auto updated2 = dprint_detail::update_format_string<sizeof(format2), int, const char*>(format2);
    static_assert(updated2.check("Some number {0:d}, and some text {1:s}\n"),
                  "Updated format string should match expected output");

    // *** NEW: Example using update_format_string_from_args for dprint_strings section storage ***

    // Example 3: Generate constexpr format string that can be stored in dprint_strings section
    constexpr auto updated_format_for_storage =
        dprint_detail::update_format_string_from_args("Debug: value={} status={}\n", 42, "ok");
    // This constexpr result can be used to create a string in dprint_strings section

    // Verify the generated format string is correct - now outputs {0:d} instead of {d}
    static_assert(updated_format_for_storage.data[13] == '{', "Opening brace for first placeholder");
    static_assert(updated_format_for_storage.data[14] == '0', "First index should be '0'");
    static_assert(updated_format_for_storage.data[15] == ':', "Colon separator");
    static_assert(updated_format_for_storage.data[16] == 'd', "First value should be 'd' for int");
    static_assert(updated_format_for_storage.data[17] == '}', "Closing brace for first placeholder");

    // Example 4: Multiple examples showing constexpr format generation
    constexpr auto simple_format = dprint_detail::update_format_string_from_args("Number: {}\n", 123);
    static_assert(simple_format.check("Number: {0:d}\n"), "Simple format should have {0:d} for int");

    constexpr auto float_format = dprint_detail::update_format_string_from_args("Pi: {}\n", 3.14f);
    static_assert(float_format.check("Pi: {0:f}\n"), "Float format should have {0:f} for float");

    constexpr auto multi_format = dprint_detail::update_format_string_from_args("Data: {} {} {}\n", 42, 'x', "test");
    static_assert(multi_format.check("Data: {0:d} {1:c} {2:s}\n"),
                  "Multi format should have {0:d}, {1:c}, {2:s} for int, char, const char*");

    // Example 5: Complex types with verification
    constexpr char format3[] = "Values: {}, {}, {}, {}\n";
    constexpr auto updated3 = dprint_detail::update_format_string<sizeof(format3), int, float, char, bool>(format3);
    static_assert(updated3.check("Values: {0:d}, {1:f}, {2:c}, {3:d}\n"),
                  "Updated format string should match expected output");

    // Example 6: Unsigned and pointer types
    constexpr char format4[] = "Unsigned: {}, Pointer: {}\n";
    constexpr auto updated4 = dprint_detail::update_format_string<sizeof(format4), unsigned int, void*>(format4);
    static_assert(updated4.check("Unsigned: {0:u}, Pointer: {1:s}\n"),
                  "Updated format string should match expected output");
}

void dprint_format_update_tests() {
    // Compile-time tests with static_assert to verify core functionality

    // Test type character mapping validation
    static_assert(dprint_detail::get_type_char<int>() == 'd', "int maps to 'd'");
    static_assert(dprint_detail::get_type_char<unsigned int>() == 'u', "unsigned int maps to 'u'");
    static_assert(dprint_detail::get_type_char<float>() == 'f', "float maps to 'f'");
    static_assert(dprint_detail::get_type_char<char>() == 'c', "char maps to 'c'");
    static_assert(dprint_detail::get_type_char<const char*>() == 's', "const char* maps to 's'");
    static_assert(dprint_detail::get_type_char<char*>() == 's', "char* maps to 's'");
    static_assert(dprint_detail::get_type_char<bool>() == 'd', "bool maps to 'd'");

    // Test placeholder counting at compile-time with literal strings
    static_assert(dprint_detail::count_placeholders("Values: {} and {}\n") == 2, "Should count 2 placeholders");
    static_assert(dprint_detail::count_placeholders("Number: {}\n") == 1, "Should count 1 placeholder");
    static_assert(dprint_detail::count_placeholders("No braces here\n") == 0, "Should count 0 placeholders");

    // Test 1: Basic functionality verification - now outputs with explicit index
    constexpr auto updated1 = dprint_detail::update_format_string_from_args("Number: {}\n", 42);
    static_assert(updated1.check("Number: {0:d}\n"), "Updated format should match expected output");

    // Test 2: Verify the function generates constexpr results that can be stored
    constexpr auto format_for_storage = dprint_detail::update_format_string_from_args("Test: {}\n", 123);
    static_assert(format_for_storage.check("Test: {0:d}\n"), "Format for storage should match expected output");

    // Test 3: Multiple types verification - focus on type character generation
    constexpr auto updated3 = dprint_detail::update_format_string_from_args("Float: {}\n", 3.14f);
    static_assert(updated3.check("Float: {0:f}\n"), "Updated format should match expected output");

    constexpr auto updated4 = dprint_detail::update_format_string_from_args("Char: {}\n", 'x');
    static_assert(updated4.check("Char: {0:c}\n"), "Updated format should match expected output");

    constexpr auto updated5 = dprint_detail::update_format_string_from_args("Unsigned: {}\n", 42u);
    static_assert(updated5.check("Unsigned: {0:u}\n"), "Updated format should match expected output");

    // Test 4: Pointer types verification
    constexpr char* test_ptr = nullptr;
    constexpr auto updated6 = dprint_detail::update_format_string_from_args("Ptr: {}\n", test_ptr);
    static_assert(updated6.check("Ptr: {0:s}\n"), "Updated format should match expected output");

    // Test 5: Verify original user requirement works - now with explicit indices
    constexpr auto updated_original =
        dprint_detail::update_format_string_from_args("Some number {}, and some text {}\n", 42, "hello");
    static_assert(updated_original.check("Some number {0:d}, and some text {1:s}\n"),
                  "Original requirement should work");
}

void dprint_indexed_format_tests() {
    // Tests for indexed placeholder format (fmtlib-compatible)

    // Test 1: Simple indexed format - single argument with index
    constexpr auto indexed1 = dprint_detail::update_format_string_from_args("Simple: n = {0}\n", 42);
    static_assert(indexed1.check("Simple: n = {0:d}\n"), "Indexed format should preserve index and add type");

    // Test 2: Repeated index - same argument referenced multiple times
    constexpr auto indexed2 = dprint_detail::update_format_string_from_args("Repeat: n = {0}, n = {0}\n", 42);
    static_assert(indexed2.check("Repeat: n = {0:d}, n = {0:d}\n"), "Repeated index should work");

    // Test 3: Multiple arguments with indices in different order
    constexpr auto indexed3 =
        dprint_detail::update_format_string_from_args("Test3: n = {0}, i = {1}, n = {0}\n", 42, 5);
    static_assert(indexed3.check("Test3: n = {0:d}, i = {1:d}, n = {0:d}\n"),
                  "Multiple indices with repetition should work");

    // Test 4: Out of order indices
    constexpr auto indexed4 = dprint_detail::update_format_string_from_args("Order: {1}, {0}\n", 42, 5);
    static_assert(indexed4.check("Order: {1:d}, {0:d}\n"), "Out of order indices should work");

    // Test 5: Detect mixed placeholder styles
    static_assert(dprint_detail::has_mixed_placeholders("Mixed: {} and {0}\n"), "Should detect mixed placeholders");
    static_assert(!dprint_detail::has_mixed_placeholders("Not mixed: {} and {}\n"), "Should not flag all non-indexed");
    static_assert(!dprint_detail::has_mixed_placeholders("Not mixed: {0} and {1}\n"), "Should not flag all indexed");

    // Test 6: Validation helpers
    static_assert(dprint_detail::all_arguments_referenced("All ref: {0} {1}\n", 2), "Both args referenced");
    static_assert(!dprint_detail::all_arguments_referenced("Missing: {0}\n", 2), "Arg 1 not referenced");
    static_assert(dprint_detail::get_max_index("Max: {0} {2} {1}\n") == 2, "Max index should be 2");
}

void dprint_indexed_format_failure_tests() {
    // These tests demonstrate format strings that should NOT compile
    // Uncomment any of these to verify they produce compile-time errors

    // Failure 1: Mixed indexed and non-indexed placeholders
    // DPRINT("Failure: n = {}, n = {0}\n", 42);
    // Expected error: "Cannot mix indexed ({0}) and non-indexed ({}) placeholders"

    // Failure 2: Index out of bounds
    // DPRINT("Bad index: n = {1}\n", 42);
    // Expected error: "Placeholder index exceeds number of arguments"

    // Failure 3: Not all arguments referenced
    // DPRINT("Unreferenced: n = {0}\n", 42, 5);
    // Expected error: "All arguments must be referenced when using indexed placeholders"
}

int main() {
    some_function(5);
    test_indexed_placeholders(42);
    halt();
    return 0;
}
