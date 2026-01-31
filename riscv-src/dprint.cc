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
    static_assert(result.check("Test: {d} and {s}\n"), "Resulting format string should match expected output");
}

void demonstrate_format_string_usage() {
    // Examples of how to use the update_format_string function with validation

    // Example 1: Valid usage - arguments match placeholders
    constexpr char format1[] = "Processing item {} with status {}\n";
    constexpr auto updated1 = dprint_detail::update_format_string<sizeof(format1), int, const char*>(format1);
    static_assert(updated1.check("Processing item {d} with status {s}\n"),
                  "Updated format string should match expected output");

    // Example 2: Original user requirement with verification
    constexpr char format2[] = "Some number {}, and some text {}\n";
    constexpr auto updated2 = dprint_detail::update_format_string<sizeof(format2), int, const char*>(format2);
    static_assert(updated2.check("Some number {d}, and some text {s}\n"),
                  "Updated format string should match expected output");

    // *** NEW: Example using update_format_string_from_args for dprint_strings section storage ***

    // Example 3: Generate constexpr format string that can be stored in dprint_strings section
    constexpr auto updated_format_for_storage =
        dprint_detail::update_format_string_from_args("Debug: value={} status={}\n", 42, "ok");
    // This constexpr result can be used to create a string in dprint_strings section

    // Verify the generated format string is correct
    static_assert(updated_format_for_storage.data[13] == '{', "Opening brace for first placeholder");
    static_assert(updated_format_for_storage.data[14] == 'd', "First value should be 'd' for int");
    static_assert(updated_format_for_storage.data[15] == '}', "Closing brace for first placeholder");
    static_assert(updated_format_for_storage.data[24] == '{', "Opening brace for second placeholder");
    static_assert(updated_format_for_storage.data[25] == 's', "Second value should be 's' for const char*");
    static_assert(updated_format_for_storage.data[26] == '}', "Closing brace for second placeholder");

    // Example 4: Multiple examples showing constexpr format generation
    constexpr auto simple_format = dprint_detail::update_format_string_from_args("Number: {}\n", 123);
    static_assert(simple_format.check("Number: {d}\n"), "Simple format should have {d} for int");

    constexpr auto float_format = dprint_detail::update_format_string_from_args("Pi: {}\n", 3.14f);
    static_assert(float_format.check("Pi: {f}\n"), "Float format should have {f} for float");

    constexpr auto multi_format = dprint_detail::update_format_string_from_args("Data: {} {} {}\n", 42, 'x', "test");
    static_assert(multi_format.check("Data: {d} {c} {s}\n"),
                  "Multi format should have {d}, {c}, {s} for int, char, const char*");

    // Example 5: Complex types with verification
    constexpr char format3[] = "Values: {}, {}, {}, {}\n";
    constexpr auto updated3 = dprint_detail::update_format_string<sizeof(format3), int, float, char, bool>(format3);
    static_assert(updated3.check("Values: {d}, {f}, {c}, {d}\n"), "Updated format string should match expected output");

    // Example 6: Unsigned and pointer types
    constexpr char format4[] = "Unsigned: {}, Pointer: {}\n";
    constexpr auto updated4 = dprint_detail::update_format_string<sizeof(format4), unsigned int, void*>(format4);
    static_assert(updated4.check("Unsigned: {u}, Pointer: {s}\n"),
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

    // Test 1: Basic functionality verification - the function returns a result with correct size
    constexpr auto updated1 = dprint_detail::update_format_string_from_args("Number: {}\n", 42);
    static_assert(updated1.check("Number: {d}\n"), "Updated format should match expected output");

    // Test 2: Verify the function generates constexpr results that can be stored
    constexpr auto format_for_storage = dprint_detail::update_format_string_from_args("Test: {}\n", 123);
    static_assert(format_for_storage.check("Test: {d}\n"), "Format for storage should match expected output");

    // Test 3: Multiple types verification - focus on type character generation
    constexpr auto updated3 = dprint_detail::update_format_string_from_args("Float: {}\n", 3.14f);
    static_assert(updated3.check("Float: {f}\n"), "Updated format should match expected output");

    constexpr auto updated4 = dprint_detail::update_format_string_from_args("Char: {}\n", 'x');
    static_assert(updated4.check("Char: {c}\n"), "Updated format should match expected output");

    constexpr auto updated5 = dprint_detail::update_format_string_from_args("Unsigned: {}\n", 42u);
    static_assert(updated5.check("Unsigned: {u}\n"), "Updated format should match expected output");

    // Test 4: Pointer types verification
    constexpr char* test_ptr = nullptr;
    constexpr auto updated6 = dprint_detail::update_format_string_from_args("Ptr: {}\n", test_ptr);
    static_assert(updated6.check("Ptr: {s}\n"), "Updated format should match expected output");

    // Test 5: Verify original user requirement works - demonstrate functionality without exact position checks
    constexpr auto updated_original =
        dprint_detail::update_format_string_from_args("Some number {}, and some text {}\n", 42, "hello");
    static_assert(updated_original.check("Some number {d}, and some text {s}\n"), "Original requirement should work");
}

int main() {
    some_function(5);
    halt();
    return 0;
}
