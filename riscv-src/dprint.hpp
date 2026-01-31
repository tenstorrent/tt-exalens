// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <type_traits>

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

inline volatile DebugPrintMemLayout* get_debug_print_buffer() { return (volatile DebugPrintMemLayout* const)(0x50000); }

namespace dprint_detail {
// If you see linker error about multiple definitions of this variable,
// know that multiple compile units are not allowed when using current dprint implementation.
const std::array<char, 5> single_compile_unit_forcing
    __attribute__((section("dprint_strings"), used)) = {'!', '@', '#', '$', '\0'};

constexpr std::size_t message_header_size = 1;

// Type-to-size mapping for serialization
template <typename T>
struct dprint_type_size {
    static constexpr std::size_t value = sizeof(T);
};

// Generic pointer types - serialize as 4 bytes
template <typename T>
struct dprint_type_size<T*> {
    static constexpr std::size_t value = sizeof(T*);
};

// Serialize string array as pointer
template <std::size_t N>
struct dprint_type_size<char[N]> {
    static constexpr std::size_t value = dprint_type_size<char*>::value;
};

// Serialize constant string array as pointer
template <std::size_t N>
struct dprint_type_size<const char[N]> {
    static constexpr std::size_t value = dprint_type_size<const char*>::value;
};

// TODO: Add more dprint specific types that are supported in original dprint implementation

// Helper to get size for a single type, removing cv-qualifiers and references
template <typename T>
constexpr std::size_t get_arg_size() {
    using base_type = std::remove_cv_t<std::remove_reference_t<T>>;
    return dprint_type_size<base_type>::value;
}

// Compile-time function to calculate total message size
template <typename... Args>
constexpr std::uint32_t calculate_dprint_message_size() {
    // Sum up sizes of all argument types
    return (get_arg_size<Args>() + ...);
}

// Wrapper function that forwards argument types but ignores values
// This allows calling with actual arguments: calculate_dprint_message_size_from_args(arg1, arg2, ...)
template <typename... Args>
constexpr std::uint32_t calculate_dprint_message_size_from_args(const Args&... args) {
    (void)((void)args, ...);  // Suppress unused parameter warnings for all args
    return message_header_size + calculate_dprint_message_size<Args...>();
}

// ----------------------------------------------------------------------------------------
// Format string update functionality
// ----------------------------------------------------------------------------------------

// Type-to-character mapping for format strings
template <typename T>
struct dprint_type_to_char {
    static constexpr char value = '?';  // Unknown type default
};

// Specializations for different types
template <>
struct dprint_type_to_char<int> {
    static constexpr char value = 'd';
};
template <>
struct dprint_type_to_char<unsigned int> {
    static constexpr char value = 'u';
};
template <>
struct dprint_type_to_char<long> {
    static constexpr char value = 'd';
};
template <>
struct dprint_type_to_char<unsigned long> {
    static constexpr char value = 'u';
};
template <>
struct dprint_type_to_char<long long> {
    static constexpr char value = 'd';
};
template <>
struct dprint_type_to_char<unsigned long long> {
    static constexpr char value = 'u';
};
template <>
struct dprint_type_to_char<short> {
    static constexpr char value = 'd';
};
template <>
struct dprint_type_to_char<unsigned short> {
    static constexpr char value = 'u';
};
template <>
struct dprint_type_to_char<char> {
    static constexpr char value = 'c';
};
template <>
struct dprint_type_to_char<unsigned char> {
    static constexpr char value = 'c';
};
template <>
struct dprint_type_to_char<float> {
    static constexpr char value = 'f';
};
template <>
struct dprint_type_to_char<double> {
    static constexpr char value = 'f';
};
template <>
struct dprint_type_to_char<bool> {
    static constexpr char value = 'd';
};

// Pointer types (including strings)
template <typename T>
struct dprint_type_to_char<T*> {
    static constexpr char value = 's';
};
template <>
struct dprint_type_to_char<char*> {
    static constexpr char value = 's';
};
template <>
struct dprint_type_to_char<const char*> {
    static constexpr char value = 's';
};

// Array types (treat as strings)
template <std::size_t N>
struct dprint_type_to_char<char[N]> {
    static constexpr char value = 's';
};
template <std::size_t N>
struct dprint_type_to_char<const char[N]> {
    static constexpr char value = 's';
};

// Helper to get type character for a single type, removing cv-qualifiers and references
template <typename T>
constexpr char get_type_char() {
    using base_type = std::remove_cv_t<std::remove_reference_t<T>>;
    return dprint_type_to_char<base_type>::value;
}

// Compile-time string class for building the result
template <std::size_t N>
struct static_string {
    char data[N + 1];
    std::size_t size;

    constexpr static_string() : data{}, size(0) {}

    constexpr void push_back(char c) {
        if (size < N) {
            data[size++] = c;
            data[size] = '\0';  // Ensure null termination
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

    // Helper to create a compact array of the actual used size
    template <std::size_t... Is>
    constexpr std::array<char, sizeof...(Is)> to_compact_array_impl(std::index_sequence<Is...>) const {
        return {{data[Is]...}};
    }

    // Returns an array sized exactly to fit the string content (size + 1 for null terminator)
    constexpr auto to_compact_array() const { return to_compact_array_impl(std::make_index_sequence<size + 1>{}); }

    template <std::size_t M>
    constexpr bool check(const char (&expected)[M]) const {
        if (size != M - 1) return false;
        for (std::size_t i = 0; i < size; ++i) {
            if (data[i] != expected[i]) return false;
        }
        return true;
    }

    constexpr const char* c_str() const { return data; }
};

// Helper to check if a character is a digit
constexpr bool is_digit(char c) { return c >= '0' && c <= '9'; }

// Helper struct to return both parsed value and new position
struct ParseResult {
    int value;
    std::size_t new_pos;
};

// Helper to parse an integer from format string starting at position i
// Returns the parsed value and the new position after the digits
constexpr ParseResult parse_index(const char* format, std::size_t i, std::size_t format_len) {
    int value = 0;
    std::size_t pos = i;
    while (pos < format_len && is_digit(format[pos])) {
        value = value * 10 + (format[pos] - '0');
        ++pos;
    }
    return ParseResult{value, pos};
}

// Token types for format string parsing
enum class TokenType {
    Placeholder,         // {} or {N}
    EscapedOpenBrace,    // {{
    EscapedCloseBrace,   // }}
    InvalidPlaceholder,  // Invalid { sequence
    RegularChar          // Any other character
};

// Result of parsing a single token from format string
struct FormatToken {
    TokenType type;
    std::size_t end_pos;  // Position to continue parsing from (after this token)
    bool is_indexed;      // true if {N}, false if {}
    int index;            // The N in {N}, or -1 for {} or escape sequences
};

// Parse a single token from the format string at position i
// This is the main tokenizer that handles all format string elements:
// - Placeholders: {} and {N}
// - Escape sequences: {{ and }}
// - Regular characters
template <std::size_t N>
constexpr FormatToken parse_format_token(const char (&format)[N], std::size_t i) {
    constexpr std::size_t format_len = N - 1;

    if (i >= format_len) {
        return FormatToken{TokenType::RegularChar, i + 1, false, -1};
    }

    char c = format[i];

    // Check for escaped opening brace {{
    if (c == '{' && i + 1 < format_len && format[i + 1] == '{') {
        return FormatToken{TokenType::EscapedOpenBrace, i + 2, false, -1};
    }

    // Check for escaped closing brace }}
    if (c == '}' && i + 1 < format_len && format[i + 1] == '}') {
        return FormatToken{TokenType::EscapedCloseBrace, i + 2, false, -1};
    }

    // Check for placeholder {N} or {}
    if (c == '{') {
        if (i + 1 >= format_len) {
            // '{' at end of string is invalid
            return FormatToken{TokenType::InvalidPlaceholder, i + 1, false, -1};
        }

        if (is_digit(format[i + 1])) {
            // Indexed placeholder {N}
            ParseResult result = parse_index(format, i + 1, format_len);
            if (result.new_pos < format_len && format[result.new_pos] == '}') {
                return FormatToken{TokenType::Placeholder, result.new_pos + 1, true, result.value};
            }
            // Invalid: digit not followed by }
            return FormatToken{TokenType::InvalidPlaceholder, i + 1, false, -1};
        } else if (format[i + 1] == '}') {
            // Non-indexed placeholder {}
            return FormatToken{TokenType::Placeholder, i + 2, false, -1};
        }

        // Invalid: '{' not followed by '{', '}', or digit
        return FormatToken{TokenType::InvalidPlaceholder, i + 1, false, -1};
    }

    // Regular character
    return FormatToken{TokenType::RegularChar, i + 1, false, -1};
}

// Helper to detect if format string uses indexed placeholders ({0}, {1}, etc.)
// Returns true if ANY placeholder has an index
template <std::size_t N>
constexpr bool has_indexed_placeholders(const char (&format)[N]) {
    for (std::size_t i = 0; i < N - 1;) {
        FormatToken token = parse_format_token(format, i);
        if (token.type == TokenType::Placeholder && token.is_indexed) {
            return true;
        }
        i = token.end_pos;
    }
    return false;
}

// Helper to check for mixed placeholder styles (both {} and {N})
// This should fail validation per fmtlib rules
template <std::size_t N>
constexpr bool has_mixed_placeholders(const char (&format)[N]) {
    bool found_indexed = false;
    bool found_unindexed = false;

    for (std::size_t i = 0; i < N - 1;) {
        FormatToken token = parse_format_token(format, i);
        if (token.type == TokenType::Placeholder) {
            if (token.is_indexed) {
                found_indexed = true;
            } else {
                found_unindexed = true;
            }
            if (found_indexed && found_unindexed) {
                return true;
            }
        }
        i = token.end_pos;
    }
    return false;
}

// Helper to validate that all arguments are referenced in indexed format
// Returns true if all argument indices from 0 to arg_count-1 are used at least once
template <std::size_t N>
constexpr bool all_arguments_referenced(const char (&format)[N], std::size_t arg_count) {
    if (arg_count == 0) return true;

    // Track which arguments are referenced (up to 32 arguments)
    bool referenced[32] = {};
    if (arg_count > 32) return false;  // Limit for simplicity

    for (std::size_t i = 0; i < N - 1;) {
        FormatToken token = parse_format_token(format, i);
        if (token.type == TokenType::Placeholder && token.is_indexed) {
            if (token.index >= 0 && static_cast<std::size_t>(token.index) < arg_count) {
                referenced[token.index] = true;
            }
        }
        i = token.end_pos;
    }

    // Check that all arguments from 0 to arg_count-1 are referenced
    for (std::size_t i = 0; i < arg_count; ++i) {
        if (!referenced[i]) return false;
    }
    return true;
}

// Helper to find the maximum index used in format string
template <std::size_t N>
constexpr int get_max_index(const char (&format)[N]) {
    int max_index = -1;
    for (std::size_t i = 0; i < N - 1;) {
        FormatToken token = parse_format_token(format, i);
        if (token.type == TokenType::Placeholder && token.is_indexed) {
            if (token.index > max_index) {
                max_index = token.index;
            }
        }
        i = token.end_pos;
    }
    return max_index;
}

// Helper to count placeholders in format string at compile time
template <std::size_t N>
constexpr std::size_t count_placeholders(const char (&format)[N]) {
    std::size_t count = 0;
    for (std::size_t i = 0; i < N - 1;) {
        FormatToken token = parse_format_token(format, i);
        if (token.type == TokenType::Placeholder && !token.is_indexed) {
            ++count;
        }
        i = token.end_pos;
    }
    return count;
}

// Helper to validate format string for invalid brace sequences
// Returns true if format string is valid, false if it contains errors
template <std::size_t N>
constexpr bool is_valid_format_string(const char (&format)[N]) {
    for (std::size_t i = 0; i < N - 1;) {
        FormatToken token = parse_format_token(format, i);

        // Check for invalid placeholder syntax
        if (token.type == TokenType::InvalidPlaceholder) {
            return false;
        }

        i = token.end_pos;
    }
    return true;
}

// Main function to update format string with type information
// Supports both {} and {N} placeholder styles (fmtlib-compatible)
template <std::size_t N, typename... Args>
constexpr auto update_format_string(const char (&format)[N]) {
    constexpr std::size_t format_len = N - 1;  // Exclude null terminator
    constexpr std::size_t arg_count = sizeof...(Args);

    // Detect if we're using indexed placeholders
    bool indexed = has_indexed_placeholders(format);

    // Calculate maximum result length:
    // - Original format length
    // - Each {} or {N} can add at most 2 extra characters (":X")
    // - Assuming worst case of format_len/2 placeholders (every other char is {)
    // Use a reasonable upper bound
    constexpr std::size_t result_len = format_len + (format_len / 2 + 1) * 2;

    static_string<result_len> result;

    constexpr char type_chars[] = {get_type_char<Args>()...};
    std::size_t type_index = 0;

    for (std::size_t i = 0; i < format_len;) {
        FormatToken token = parse_format_token(format, i);

        if (token.type == TokenType::EscapedOpenBrace) {
            // Preserve escaped opening brace: {{
            result.push_back('{');
            result.push_back('{');
        } else if (token.type == TokenType::EscapedCloseBrace) {
            // Preserve escaped closing brace: }}
            result.push_back('}');
            result.push_back('}');
        } else if (token.type == TokenType::Placeholder) {
            // Determine the argument index for this placeholder
            int arg_index = token.is_indexed ? token.index : type_index++;

            // Unified handling for both indexed and non-indexed: output {index:type}
            result.push_back('{');

            // Output the index
            if (arg_index >= 10) {
                result.push_back('0' + (arg_index / 10));
            }
            result.push_back('0' + (arg_index % 10));

            // Add colon and type character
            result.push_back(':');
            if (arg_index >= 0 && static_cast<std::size_t>(arg_index) < sizeof...(Args)) {
                result.push_back(type_chars[arg_index]);
            } else {
                result.push_back('?');  // Fallback for extra placeholders
            }
            result.push_back('}');
        } else if (token.type == TokenType::InvalidPlaceholder) {
            // Invalid placeholder - should be caught by validation, but copy as-is if we get here
            result.push_back(format[i]);
        } else {
            // Regular character
            result.push_back(format[i]);
        }

        i = token.end_pos;
    }

    return result;
}

// New function that returns constexpr updated format string from arguments
// This allows calling with actual arguments: update_format_string_from_args("format {}", arg1, arg2, ...)
template <std::size_t N, typename... Args>
constexpr auto update_format_string_from_args(const char (&format)[N], const Args&... args) {
    (void)((void)args, ...);  // Suppress unused parameter warnings for all args
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
// - strings should be coded with 's' so that host knows to visualize them (if they are part of strings section, print
// like that, if not, print by reading from device)
// - we won't use STRING_INDEX to compress strings used in dprint as it is hard thing to solve

// Regarding dprint_format string, if we don't want to have a hustle with kernel_id, etc.
// We can encode kernel_id into string table
// What we can do is make firmware string table start at 10MB.
// Then every kernel during compilation can have string table start at 10MB + kernel_id * 50KB.
// Host would be able to figure out all kernel_ids out of it.
// Problem with this solution is that we will map all virtual memory to only string tables and none can use similar
// trick. Simpler solution is that firmware string table starts at 10MB. Kernel string table starts at 11MB. But firmare
// after running kernel, needs to wait for dprint to be drained. Similar solution would be with string index. There
// should be global variable that is set when kernel start and cleared when kernel ends. Also, dprint buffer should be
// drained before and after kernel call...

// If we want to have single buffer for all riscs, we need to encode risc id as well.
// So every dprint message would have header like this: (1b risc_id, 2b kernel_id, 1b string_index)
// This avoids potential race conditions with needing to drain dprint queue, unless we require drain to get dprint write
// lock. Since risc_id is known during compile time, we might be able to encode both risc_id and string_index into 2b
// value as compiler will do that in compile time... Should be tested... Regarding dprint write lock, blackhole and
// quasar have atomic, but wormhole doesn't What can be done for wormhole is use L1 location similar to other archs, but
// instead of using atomic, do simple trick: void take_dprint_lock(uint32_t risc_id) {
//     while (true) {
//         // Wait for sync to be -1, meaning there is no lock
//         while (sync != -1);
//
//         // Try taking lock by setting sync to risc_id
//         sync = risc_id;
//
//         // As there can be race condition in reading (multiple riscs can read sync == -1 at similar time)
//         // they shouldn't be able to write to L1 at the same time, which means only slowest one will make sync with
//         its risc_id
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
// Why this implementation might be ok... Because DPRINT is debugging path and we might not care if dprint take 120
// cycles instead of 100 cycles.
//
// Final solution for single buffer shared among riscs, firmwares and kernels.
// We will refer to dprint stream as a stream of bytes that host reads from dprint buffer (or that device writes to same
// buffer). We will address reading/writing from/to dprint buffer later.
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
// - From elf, it loads DPrintStringInfo structure by indexing dprint_strings_info section with info_id (it represents
// index of array in that section)
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
//       uint8_t kernel_printed[MAX_KERNELS]; // Array of flags that say if kernel has printed dprint or not since
//       starting uint8_t data[DPRINT_BUFFER_SIZE];
//   };
// - When any risc wants to do dprint, it takes lock (using atomic or other mechanism)
// - After taking a lock, it waits for enough space in dprint buffer to write its dprint message (in case when host
// needs to drain the stream).
// - If kernel is writing dprint for the first time after starting, it writes 0xFFFF followed by risc_id and kernel_id.
// (Either kernel _start or firmware main will update kernel_printed flag to 0 if it is compiled with dprint)
// - It writes DPrintHeader structure (is_kernel, risc_id, info_id) to dprint buffer followed by the serialized
// arguments.
// - It releases the lock.
// DEVICE COMPILE TIME MAGIC:
// - During dprint compilation, format string should look like this:
//   DPRINT("Some message: {}\n", arg);
// - Compiler will test number of arguments against number of {} placeholders.
// - Compiler will generate updated format string with type information:
//   "Some message: {d}\n" (assuming arg is int)
// - Compiler will create string in dprint_strings section for the updated format string.
// - Compiler will create DPrintStringInfo structure in dprint_strings_info section with pointer to format string, file
// name and line number.
// - Compiler will generate index of DPrintStringInfo structure in dprint_strings_info section and store it in
// DPrintHeader (along with is_kernel and risc_id).
// - Since compiler knows all argument types, during runtime it can serialize arguments properly.
//
// Reading and writting from/to dprint buffer:
//
// HOST:
// - Reads dprint buffer read/write positions to know how much data is available to read.
// - If write position is bigger than read position, if can read from read position to write position.
// - If write position is smaller than read position, it means buffer wrapped around, so it reads from read position to
// end of buffer and then from beginning of buffer to write position.
// - After reading data, it updates read position in dprint buffer.
//
// DEVICE:
// - When kernel wants to do dprint, it first checks if kernel_printed[risc_id] is 0.
// - If it is 0, it reads current kernel_id from mailboxes_t for that risc and sets kernel_printed[risc_id] to 1.
// - It takes writers lock. (THIS NEEDS TO BE EXPLAINED PER ARCHITECTURE)
// - If local variable for kernel_id is not 0 (meaning it is a subsequent dprint), it will want to write 0xFFFF followed
// by kernel_id and risc_id to the dprint buffer.
// - Before any argument writing, it checks if there is enough space in dprint buffer to write the argument (or if we
// want to optimize device code size/speed, space for the whole message) and waits for it if there isn't enough.
// - It writes DPrintHeader structure (that was generated at compile time) to dprint buffer.
// - It writes serialized arguments to dprint buffer.
// - It releases the writers lock.
// - If we want to do circular buffer, we need to have different ways of writing:
//   - if there is enough space from write position to end of buffer, we can do single write
//   - if there isn't enough space, we need to do two writes: from write position to end of buffer and from beginning of
//   buffer to remaining size
//   - this writes should happend per argument
}  // namespace dprint_detail

#define STRING_INDEX(var, str)                                                                                      \
    {                                                                                                               \
        static constexpr char allocated_string[] __attribute__((section("dprint_strings"), used)) = str;            \
        static const char* allocated_string_in_table __attribute__((section("dprint_strings_index"), used)) =       \
            allocated_string;                                                                                       \
        /* TODO: Do we want to have structure that has detailed description (like file, line, etc.) instead of just \
         * string pointer? */                                                                                       \
    }                                                                                                               \
    constexpr uint32_t var = __COUNTER__;

// NEW: Simplified macro to create updated format string and store it in dprint_strings section
// This macro generates the updated format string at compile time and stores it
#define UPDATED_STRING_INDEX(var, format, ...)                                                                \
    {                                                                                                         \
        constexpr auto updated_format = dprint_detail::update_format_string_from_args(format, ##__VA_ARGS__); \
        static const auto allocated_string __attribute__((section("dprint_strings"), used)) =                 \
            updated_format.to_array();                                                                        \
        static const char* allocated_string_in_table __attribute__((section("dprint_strings_index"), used)) = \
            allocated_string.data();                                                                          \
    }                                                                                                         \
    constexpr uint32_t var = __COUNTER__;

#define DPRINT(format, ...)                                                                                            \
    {                                                                                                                  \
        /* Validate format string syntax */                                                                            \
        static_assert(dprint_detail::is_valid_format_string(format),                                                   \
                      "Invalid format string: unescaped '{' must be followed by '{', '}', or a digit");                \
        /* Validate placeholder format */                                                                              \
        static_assert(!dprint_detail::has_mixed_placeholders(format),                                                  \
                      "Cannot mix indexed ({0}) and non-indexed ({}) placeholders in the same format string");         \
        /* For non-indexed placeholders, count must match argument count */                                            \
        static_assert(dprint_detail::has_indexed_placeholders(format) ||                                               \
                          dprint_detail::count_placeholders(format) == dprint_detail::count_arguments(__VA_ARGS__),    \
                      "Number of {} placeholders must match number of arguments");                                     \
        /* For indexed placeholders, validate all arguments are referenced */                                          \
        static_assert(                                                                                                 \
            !dprint_detail::has_indexed_placeholders(format) ||                                                        \
                dprint_detail::all_arguments_referenced(format, dprint_detail::count_arguments(__VA_ARGS__)),          \
            "All arguments must be referenced when using indexed placeholders");                                       \
        /* For indexed placeholders, validate no index exceeds argument count */                                       \
        static_assert(                                                                                                 \
            !dprint_detail::has_indexed_placeholders(format) ||                                                        \
                dprint_detail::get_max_index(format) < static_cast<int>(dprint_detail::count_arguments(__VA_ARGS__)),  \
            "Placeholder index exceeds number of arguments");                                                          \
        UPDATED_STRING_INDEX(dprint_format_index, format, __VA_ARGS__);                                                \
        using format_index_t = uint8_t;                                                                                \
        static_assert(dprint_format_index <= std::numeric_limits<format_index_t>::max(),                               \
                      "Too many DPRINT calls, exceeds limit");                                                         \
        constexpr auto message_size = dprint_detail::calculate_dprint_message_size_from_args(__VA_ARGS__);             \
        static_assert(message_size <= DPRINT_BUFFER_SIZE, "Not implemented: DPRINT message size exceeds buffer size"); \
        /* TODO: Check if we should wait for dprint buffer to get drained because there isn't enough space to          \
         * serialize current dprint */                                                                                 \
        /* TODO: Call serialization */                                                                                 \
        volatile DebugPrintMemLayout* dprint_buffer = get_debug_print_buffer();                                        \
        dprint_buffer->data[dprint_buffer->aux.wpos] = dprint_format_index;                                            \
        dprint_buffer->aux.wpos = dprint_buffer->aux.wpos + 1;                                                         \
    }
