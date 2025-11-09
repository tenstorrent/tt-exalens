// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

#include <cstdint>
#include <cstddef>
#include <limits>
#include <type_traits>
#include <array>

#define ATTR_PACK __attribute__((packed))

constexpr static std::uint32_t DPRINT_BUFFER_SIZE = 204;  // per thread
struct DebugPrintMemLayout {
    struct Aux {
        // current writer offset in buffer
        uint32_t wpos;
        uint32_t rpos;
        uint16_t core_x;
        uint16_t core_y;
    } aux ATTR_PACK;
    uint8_t data[DPRINT_BUFFER_SIZE - sizeof(Aux)];

    static size_t rpos_offs() { return offsetof(DebugPrintMemLayout::Aux, rpos) + offsetof(DebugPrintMemLayout, aux); }

} ATTR_PACK;

inline volatile DebugPrintMemLayout* get_debug_print_buffer() {
    return (volatile DebugPrintMemLayout * const)(0x50000);
}

namespace dprint_detail {
    // If you see linker error about multiple definitions of this variable,
    // know that multiple compile units are not allowed when using current dprint implementation.
    const std::array<char, 5> single_compile_unit_forcing __attribute__((section("dprint_strings"), used)) = {'!', '@', '#', '$', '\0'};

    constexpr std::size_t message_header_size = 1;

    // Type-to-size mapping for serialization
    template<typename T>
    struct dprint_type_size {
        static constexpr std::size_t value = sizeof(T);
    };

    // Generic pointer types - serialize as 4 bytes
    template<typename T>
    struct dprint_type_size<T*> {
        static constexpr std::size_t value = sizeof(T*);
    };

    // Serialize string array as pointer
    template<std::size_t N>
    struct dprint_type_size<char[N]> {
        static constexpr std::size_t value = dprint_type_size<char*>::value;
    };

    // Serialize constant string array as pointer
    template<std::size_t N>
    struct dprint_type_size<const char[N]> {
        static constexpr std::size_t value = dprint_type_size<const char*>::value;
    };

    // TODO: Add more dprint specific types that are supported in original dprint implementation

    // Helper to get size for a single type, removing cv-qualifiers and references
    template<typename T>
    constexpr std::size_t get_arg_size() {
        using base_type = std::remove_cv_t<std::remove_reference_t<T>>;
        return dprint_type_size<base_type>::value;
    }

    // Compile-time function to calculate total message size
    template<typename... Args>
    constexpr std::uint32_t calculate_dprint_message_size() {
        // Sum up sizes of all argument types
        return (get_arg_size<Args>() + ...);
    }

    // Wrapper function that forwards argument types but ignores values
    // This allows calling with actual arguments: calculate_dprint_message_size_from_args(arg1, arg2, ...)
    template<typename... Args>
    constexpr std::uint32_t calculate_dprint_message_size_from_args(const Args&... args) {
        (void)((void)args, ...); // Suppress unused parameter warnings for all args
        return message_header_size + calculate_dprint_message_size<Args...>();
    }

    // ----------------------------------------------------------------------------------------
    // Format string update functionality
    // ----------------------------------------------------------------------------------------

    // Type-to-character mapping for format strings
    template<typename T>
    struct dprint_type_to_char {
        static constexpr char value = '?'; // Unknown type default
    };

    // Specializations for different types
    template<> struct dprint_type_to_char<int> { static constexpr char value = 'd'; };
    template<> struct dprint_type_to_char<unsigned int> { static constexpr char value = 'u'; };
    template<> struct dprint_type_to_char<long> { static constexpr char value = 'd'; };
    template<> struct dprint_type_to_char<unsigned long> { static constexpr char value = 'u'; };
    template<> struct dprint_type_to_char<long long> { static constexpr char value = 'd'; };
    template<> struct dprint_type_to_char<unsigned long long> { static constexpr char value = 'u'; };
    template<> struct dprint_type_to_char<short> { static constexpr char value = 'd'; };
    template<> struct dprint_type_to_char<unsigned short> { static constexpr char value = 'u'; };
    template<> struct dprint_type_to_char<char> { static constexpr char value = 'c'; };
    template<> struct dprint_type_to_char<unsigned char> { static constexpr char value = 'c'; };
    template<> struct dprint_type_to_char<float> { static constexpr char value = 'f'; };
    template<> struct dprint_type_to_char<double> { static constexpr char value = 'f'; };
    template<> struct dprint_type_to_char<bool> { static constexpr char value = 'd'; };
    
    // Pointer types (including strings)
    template<typename T> struct dprint_type_to_char<T*> { static constexpr char value = 's'; };
    template<> struct dprint_type_to_char<char*> { static constexpr char value = 's'; };
    template<> struct dprint_type_to_char<const char*> { static constexpr char value = 's'; };
    
    // Array types (treat as strings)
    template<std::size_t N> struct dprint_type_to_char<char[N]> { static constexpr char value = 's'; };
    template<std::size_t N> struct dprint_type_to_char<const char[N]> { static constexpr char value = 's'; };

    // Helper to get type character for a single type, removing cv-qualifiers and references
    template<typename T>
    constexpr char get_type_char() {
        using base_type = std::remove_cv_t<std::remove_reference_t<T>>;
        return dprint_type_to_char<base_type>::value;
    }

    // Compile-time string class for building the result
    template<std::size_t N>
    struct static_string {
        char data[N + 1];
        std::size_t size;

        constexpr static_string() : data{}, size(0) {}

        constexpr void push_back(char c) {
            if (size < N) {
                data[size++] = c;
                data[size] = '\0'; // Ensure null termination
            }
        }

        constexpr std::array<char, N + 1> to_array() const {
            std::array<char, N + 1> arr = {};
            for (std::size_t i = 0; i < size; ++i) {
                arr[i] = data[i];
            }
            arr[size] = '\0';
            return arr;
        }

        template<std::size_t M>
        constexpr bool check(const char (&expected)[M]) const {
            if (size != M - 1) return false;
            for (std::size_t i = 0; i < size; ++i) {
                if (data[i] != expected[i]) return false;
            }
            return true;
        }

        constexpr const char* c_str() const { return data; }
    };

    // Helper to count placeholders in format string at compile time
    template<std::size_t N>
    constexpr std::size_t count_placeholders(const char (&format)[N]) {
        std::size_t count = 0;
        for (std::size_t i = 0; i < N - 1; ++i) { // N-1 to exclude null terminator
            if (format[i] == '{' && i + 1 < N - 1 && format[i + 1] == '}') {
                ++count;
                ++i; // Skip the '}'
            }
        }
        return count;
    }

    // Main function to update format string with type information
    template<std::size_t N, typename... Args>
    constexpr auto update_format_string(const char (&format)[N]) {
        constexpr std::size_t format_len = N - 1; // Exclude null terminator
        constexpr std::size_t arg_count = sizeof...(Args);
        
        // Note: Validation of placeholder count vs argument count should be done separately
        // due to constexpr limitations with the RISC-V compiler
        
        constexpr std::size_t result_len = format_len + sizeof...(Args); // Each {} becomes {x}, so +1 per placeholder

        static_string<result_len> result;
        
        constexpr char type_chars[] = { get_type_char<Args>()... };
        std::size_t type_index = 0;
        
        for (std::size_t i = 0; i < format_len; ++i) {
            if (format[i] == '{' && i + 1 < format_len && format[i + 1] == '}') {
                // Replace {} with {type_char}
                result.push_back('{');
                if (type_index < sizeof...(Args)) {
                    result.push_back(type_chars[type_index++]);
                } else {
                    result.push_back('?'); // Fallback for extra placeholders
                }
                result.push_back('}');
                ++i; // Skip the '}'
            } else {
                result.push_back(format[i]);
            }
        }
        
        return result;
    }
    
    // New function that returns constexpr updated format string from arguments
    // This allows calling with actual arguments: update_format_string_from_args("format {}", arg1, arg2, ...)
    template<std::size_t N, typename... Args>
    constexpr auto update_format_string_from_args(const char (&format)[N], const Args&... args) {
        (void)((void)args, ...); // Suppress unused parameter warnings for all args
        return update_format_string<N, Args...>(format);
    }

    template <typename... Args>
    constexpr std::size_t count_arguments(const Args&... args) {
        return sizeof...(Args);
    }

    // template<typename format_index_t, typename Arg...>
    // void serialize_dprint(format_index_t format_index, Arg args...) {
    //     // Check if we have enough space in the dprint buffer
    // }

    // Serialization of pointers:
    // - It will be always serialized as 4 bytes even if it is string
    // - strings should be coded with 's' so that host knows to visualize them (if they are part of strings section, print like that, if not, print by reading from device)
    // - we won't use STRING_INDEX to compress strings used in dprint as it is hard thing to solve

    // Regarding dprint_format string, if we don't want to have a hustle with kernel_id, etc.
    // We can encode kernel_id into string table
    // What we can do is make firmware string table start at 10MB.
    // Then every kernel during compilation can have string table start at 10MB + kernel_id * 50KB.
    // Host would be able to figure out all kernel_ids out of it.
    // Problem with this solution is that we will map all virtual memory to only string tables and none can use similar trick.
    // Simpler solution is that firmware string table starts at 10MB. Kernel string table starts at 11MB.
    // But firmare after running kernel, needs to wait for dprint to be drained.
    // Similar solution would be with string index. There should be global variable that is set when kernel start and cleared when kernel ends.
    // Also, dprint buffer should be drained before and after kernel call...

    // If we want to have single buffer for all riscs, we need to encode risc id as well.
    // So every dprint message would have header like this: (1b risc_id, 2b kernel_id, 1b string_index)
    // This avoids potential race conditions with needing to drain dprint queue, unless we require drain to get dprint write lock.
    // Since risc_id is known during compile time, we might be able to encode both risc_id and string_index into 2b value as
    // compiler will do that in compile time... Should be tested...
    // Regarding dprint write lock, blackhole and quasar have atomic, but wormhole doesn't
    // What can be done for wormhole is use L1 location similar to other archs, but instead of using atomic, do simple trick:
    // void take_dprint_lock(uint32_t risc_id) {
    //     while (true) {
    //         // Wait for sync to be -1, meaning there is no lock
    //         while (sync != -1);
    //
    //         // Try taking lock by setting sync to risc_id
    //         sync = risc_id;
    //
    //         // As there can be race condition in reading (multiple riscs can read sync == -1 at similar time)
    //         // they shouldn't be able to write to L1 at the same time, which means only slowest one will make sync with its risc_id
    //         // So, we want to wait some cycles until L1 is stabilized meaning all writes have finished.
    //         NOP; NOP; NOP;... NOP;
    //         // Instead of doing NOPs, we can do multiple repeated reads which will simulate the same...
    //         // Something like:
    //         // if (sync != risc_id) continue;
    //         // if (sync != risc_id) continue;
    //         // if (sync != risc_id) continue;
    //
    //         // Confirm that we got the lock
    //         if (sync == risc_id) return;
    //     }
    // }
    // Why this implementation might be ok... Because DPRINT is debugging path and we might not care if dprint take 120 cycles instead of 100 cycles.
    //
    // Final solution for single buffer shared among riscs, firmwares and kernels.
    // We will refer to dprint stream as a stream of bytes that host reads from dprint buffer (or that device writes to same buffer).
    // We will address reading/writing from/to dprint buffer later.
    //
    // There will be two sections inside the elf:
    // - dprint_strings: contains all format strings used by dprint calls and file names.
    // - dprint_strings_info: contains list of DPrintStringInfo structures.
    // struct DPrintStringInfo {
    //     const char* format; // Pointer to format string in dprint_strings section
    //     const char* file;   // Pointer to file name string in dprint_strings section
    //     uint32_t line;      // Line number
    // };
    //
    // We need 2 bytes to store dprint header:
    // struct DPrintHeader {
    //     uint8_t is_kernel: 1; // 0 = firmware, 1 = kernel
    //     uint8_t risc_id: 5;   // 0-31 risc id (supports quasar as well)
    //     uint16_t info_id: 10; // Up to 1024 dprints per risc/firmware/kernel
    // };
    // There is special value of the structure: 0xFFFF.
    // That means that output of the new kernel started. New kernel will be described with 3 bytes:
    // - risc_id (1 byte)
    // - kernel_id (2 bytes)
    //
    // HOST:
    // - It reads stream of data from dprint buffer (will be explained later how)
    // - When it sees 0xFFFF, it will read next 3 bytes to know which kernel started on which risc
    // - If it is not 0xFFFF, it parses DPrintHeader structure.
    // - Based on is_kernel flag and risc_id, it knows which elf it should read (similar to tt-triage)
    // - From elf, it loads DPrintStringInfo structure by indexing dprint_strings_info section with info_id (it represents index of array in that section)
    // - From DPrintStringInfo structure it reads format string pointer (along with file and line if needed)
    // - Format string pointer is located in dprint_strings section, so it reads format string from there
    // - It parses format string and understands how to read arguments from dprint stream.
    // - It reads arguments from dprint stream and visualizes the output based on the format string.
    //
    // DEVICE:
    // - It has dprint buffer shared among all riscs. Structure for dprint buffer should look something like this:
    //   struct DPrintBuffer {
    //       uint32_t lock;
    //       uint32_t write_position;
    //       uint32_t read_position;
    //       uint8_t kernel_printed[MAX_KERNELS]; // Array of flags that say if kernel has printed dprint or not since starting
    //       uint8_t data[DPRINT_BUFFER_SIZE];
    //   };
    // - When any risc wants to do dprint, it takes lock (using atomic or other mechanism)
    // - After taking a lock, it waits for enough space in dprint buffer to write its dprint message (in case when host needs to drain the stream).
    // - If kernel is writing dprint for the first time after starting, it writes 0xFFFF followed by risc_id and kernel_id. (Either kernel _start or firmware main will update kernel_printed flag to 0 if it is compiled with dprint)
    // - It writes DPrintHeader structure (is_kernel, risc_id, info_id) to dprint buffer followed by the serialized arguments.
    // - It releases the lock.
    // DEVICE COMPILE TIME MAGIC:
    // - During dprint compilation, format string should look like this:
    //   DPRINT("Some message: {}\n", arg);
    // - Compiler will test number of arguments against number of {} placeholders.
    // - Compiler will generate updated format string with type information:
    //   "Some message: {d}\n" (assuming arg is int)
    // - Compiler will create string in dprint_strings section for the updated format string.
    // - Compiler will create DPrintStringInfo structure in dprint_strings_info section with pointer to format string, file name and line number.
    // - Compiler will generate index of DPrintStringInfo structure in dprint_strings_info section and store it in DPrintHeader (along with is_kernel and risc_id).
    // - Since compiler knows all argument types, during runtime it can serialize arguments properly.
    //
    // Reading and writting from/to dprint buffer:
    //
    // HOST:
    // - Reads dprint buffer read/write positions to know how much data is available to read.
    // - If write position is bigger than read position, if can read from read position to write position.
    // - If write position is smaller than read position, it means buffer wrapped around, so it reads from read position to end of buffer and then from beginning of buffer to write position.
    // - After reading data, it updates read position in dprint buffer.
    //
    // DEVICE:
    // - When kernel wants to do dprint, it first checks if kernel_printed[risc_id] is 0.
    // - If it is 0, it reads current kernel_id from mailboxes_t for that risc and sets kernel_printed[risc_id] to 1.
    // - It takes writers lock. (THIS NEEDS TO BE EXPLAINED PER ARCHITECTURE)
    // - If local variable for kernel_id is not 0 (meaning it is a subsequent dprint), it will want to write 0xFFFF followed by kernel_id and risc_id to the dprint buffer.
    // - Before any argument writing, it checks if there is enough space in dprint buffer to write the argument (or if we want to optimize device code size/speed, space for the whole message) and waits for it if there isn't enough.
    // - It writes DPrintHeader structure (that was generated at compile time) to dprint buffer.
    // - It writes serialized arguments to dprint buffer.
    // - It releases the writers lock.
    // - If we want to do circular buffer, we need to have different ways of writing:
    //   - if there is enough space from write position to end of buffer, we can do single write
    //   - if there isn't enough space, we need to do two writes: from write position to end of buffer and from beginning of buffer to remaining size
    //   - this writes should happend per argument
}

#define STRING_INDEX(var, str) \
    { \
        static constexpr char allocated_string[] __attribute__((section("dprint_strings"), used)) = str; \
        static const char* allocated_string_in_table __attribute__((section("dprint_strings_index"), used)) = allocated_string; \
        /* TODO: Do we want to have structure that has detailed description (like file, line, etc.) instead of just string pointer? */ \
    } \
    constexpr uint32_t var = __COUNTER__;

// NEW: Simplified macro to create updated format string and store it in dprint_strings section
// This macro generates the updated format string at compile time and stores it
#define UPDATED_STRING_INDEX(var, format, ...) \
    { \
        constexpr auto updated_format = dprint_detail::update_format_string_from_args(format, ##__VA_ARGS__); \
        static const std::array<char, updated_format.size + 1> allocated_string __attribute__((section("dprint_strings"), used)) = updated_format.to_array(); \
        static const char* allocated_string_in_table __attribute__((section("dprint_strings_index"), used)) = allocated_string.data(); \
    } \
    constexpr uint32_t var = __COUNTER__;

#define DPRINT(format, ...) \
{ \
    static_assert(dprint_detail::count_placeholders(format) == dprint_detail::count_arguments(__VA_ARGS__), "Number of {} placeholders must match number of arguments"); \
    UPDATED_STRING_INDEX(dprint_format_index, format, __VA_ARGS__); \
    using format_index_t = uint8_t; \
    static_assert(dprint_format_index <= std::numeric_limits<format_index_t>::max(), "Too many DPRINT calls, exceeds limit"); \
    constexpr auto message_size = dprint_detail::calculate_dprint_message_size_from_args(__VA_ARGS__); \
    static_assert(message_size <= DPRINT_BUFFER_SIZE, "Not implemented: DPRINT message size exceeds buffer size"); \
    /* TODO: Check if we should wait for dprint buffer to get drained because there isn't enough space to serialize current dprint */ \
    /* TODO: Call serialization */ \
    volatile DebugPrintMemLayout* dprint_buffer = get_debug_print_buffer(); \
    dprint_buffer->data[dprint_buffer->aux.wpos] = dprint_format_index; \
    dprint_buffer->aux.wpos = dprint_buffer->aux.wpos + 1; \
}

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
    static_assert(dprint_detail::calculate_dprint_message_size<int, const char*>() == 8, "int + const char* should be 8 bytes");
    static_assert(dprint_detail::calculate_dprint_message_size<int, const char*, double>() == 16, "int + const char* + double should be 16 bytes");

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
    static_assert(dprint_detail::count_placeholders("Start {} middle {} end {}\n") == 3, "Should find exactly 3 placeholders");

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
    constexpr auto updated_format_for_storage = dprint_detail::update_format_string_from_args(
        "Debug: value={} status={}\n", 42, "ok");
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
    static_assert(multi_format.check("Data: {d} {c} {s}\n"), "Multi format should have {d}, {c}, {s} for int, char, const char*");

    // Example 5: Complex types with verification
    constexpr char format3[] = "Values: {}, {}, {}, {}\n";
    constexpr auto updated3 = dprint_detail::update_format_string<sizeof(format3), int, float, char, bool>(format3);
    static_assert(updated3.check("Values: {d}, {f}, {c}, {d}\n"), "Updated format string should match expected output");
    
    // Example 6: Unsigned and pointer types
    constexpr char format4[] = "Unsigned: {}, Pointer: {}\n";
    constexpr auto updated4 = dprint_detail::update_format_string<sizeof(format4), unsigned int, void*>(format4);
    static_assert(updated4.check("Unsigned: {u}, Pointer: {s}\n"), "Updated format string should match expected output");
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
    constexpr auto updated_original = dprint_detail::update_format_string_from_args("Some number {}, and some text {}\n", 42, "hello");
    static_assert(updated_original.check("Some number {d}, and some text {s}\n"), "Original requirement should work");
}

int main() {
    some_function(5);
    halt();
    return 0;
}
