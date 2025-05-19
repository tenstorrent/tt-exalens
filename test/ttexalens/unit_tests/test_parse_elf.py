# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
import os

from ttexalens import tt_exalens_lib as lib
from ttexalens import util as util
from ttexalens.firmware import ELF
from ttexalens.parse_elf import ParsedElfFile, read_elf, mem_access


class TestFileIfc:
    def get_binary(self, filename):
        return open(filename, "rb")


file_ifc = TestFileIfc()


def compile_test_cpp_program(program_path, program_text):
    """
    Just compile a program to get an ELF file
    """
    print(f"\nCompiling {program_path}...")
    # Run ./build/sfpi/compiler/bin/riscv32-unknown-elf-g++ -g ./test-elf.c -o test-elf on the program_text
    import os

    elf_file_name = f"{program_path}.elf"
    src_file_name = f"{program_path}.cpp"
    os.system(f"rm -f {elf_file_name}")
    with open(f"{src_file_name}", "w") as f:
        f.write(program_text)
    # Compile the program
    os.system(f"./build/sfpi/compiler/bin/riscv32-unknown-elf-g++ -g {src_file_name} -o {program_path}.elf")
    if not os.path.exists(elf_file_name):
        util.ERROR(f"ERROR: Failed to compile {src_file_name}")
        exit(1)

    return [elf_file_name, src_file_name]


def mem_reader(addr, size_bytes, elements_to_read):
    """
    A simple memory reader stub that returns addr*10 for all reads. Only for testing.
    """
    word_array = []
    element_size = size_bytes // elements_to_read
    assert element_size * elements_to_read == size_bytes, "Size not divisible by element size"
    if element_size > 4:
        element_size = 4
        elements_to_read = size_bytes // element_size
        assert element_size * elements_to_read == size_bytes, "Size not divisible by element size"
    for i in range(elements_to_read):
        value_at_addr = (addr + element_size * i) * 10
        word_array.append(value_at_addr)
    # print(
    #     f"Read {size_bytes} bytes from {addr}: {', '.join([ str(x) for x in word_array])}"
    # )
    return word_array


class TestParseElf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("TTEXALENS_PATH"):
            cls.output_dir = os.path.join(os.environ["TTEXALENS_PATH"], "build", "test", "assets")
            cls.elf_dir = os.path.join(os.environ["TTEXALENS_PATH"], "test", "test_elfs")
        else:
            cls.output_dir = os.path.join("build", "test", "assets")
            cls.elf_dir = os.path.join("test", "test_elfs")

        cls.output_dir = os.path.abspath(cls.output_dir)
        cls.elf_dir = os.path.abspath(cls.elf_dir)

        if not os.path.exists(cls.output_dir):
            os.makedirs(cls.output_dir)

    def test_simple(self):
        program_name, program_definition = "simple", {
            "program_text": """
                int GLOBAL_INT = 1234;
                int *GLOBAL_INT_PTR = &GLOBAL_INT;
                int **GLOBAL_INT_PTR_PTR = &GLOBAL_INT_PTR;
                int &GLOBAL_INT_REF = GLOBAL_INT;

                enum MY_ENUMS { MY_ENUM_A, MY_ENUM_B, MY_ENUM_C } my_enum;

                struct S_TYPE {
                    int an_int;
                    int an_int2;
                    int *an_int_ptr;
                    int &an_int_ref = GLOBAL_INT;
                    struct NESTED_S_TYPE{
                        int nested_int;
                        int nested_int2;
                    } nested_s;
                } global_s;

                namespace ns {
                    int ns_int;
                    struct ns_S_TYPE {
                        int *global_s;
                    } ns_s;
                }

                struct S_TYPE *s_ptr;

                int main() {
                    struct S_TYPE s;
                    s.an_int = 10;
                    return 0;
                }
                """
        }
        generated_files = compile_test_cpp_program(program_name, program_definition["program_text"])
        name_dict = read_elf(file_ifc, f"{program_name}.elf")
        program_path = os.path.join(TestParseElf.output_dir, program_name)
        compile_test_cpp_program(program_path, program_definition["program_text"])
        name_dict = read_elf(file_ifc, f"{program_path}.elf")

        # Variable, pointer, reference
        # As mem_access returns a type
        assert mem_access(name_dict, "GLOBAL_INT", mem_reader)[0] == [725160]
        with self.assertRaises(Exception):
            assert mem_access(name_dict, "*GLOBAL_INT", mem_reader)[0] == [0]
        assert mem_access(name_dict, "GLOBAL_INT_PTR", mem_reader)[0] == [725200]
        assert mem_access(name_dict, "GLOBAL_INT_PTR_PTR", mem_reader)[0] == [725240]
        assert mem_access(name_dict, "*GLOBAL_INT_PTR_PTR", mem_reader)[0] == [7252400]
        assert mem_access(name_dict, "**GLOBAL_INT_PTR_PTR", mem_reader)[0] == [72524000]
        with self.assertRaises(Exception):
            assert mem_access(name_dict, "***GLOBAL_INT_PTR_PTR", mem_reader)[0]  # This fails
        assert mem_access(name_dict, "*s_ptr", mem_reader)[0] == [
            7254400,
            7254440,
            7254480,
            7254520,
            7254560,
            7254600,
        ]
        assert mem_access(name_dict, "GLOBAL_INT_REF", mem_reader)[0] == [7250400]
        assert mem_access(name_dict, "global_s", mem_reader)[0] == [
            725760,
            725800,
            725840,
            725880,
            725920,
            725960,
        ]
        assert mem_access(name_dict, "global_s.an_int", mem_reader)[0] == [725760]
        assert mem_access(name_dict, "global_s.an_int2", mem_reader)[0] == [725800]
        assert mem_access(name_dict, "*global_s.an_int_ptr", mem_reader)[0] == [7258400]
        assert mem_access(name_dict, "global_s.nested_s", mem_reader)[0] == [
            725920,
            725960,
        ]
        assert mem_access(name_dict, "global_s.nested_s.nested_int", mem_reader)[0] == [725920]
        assert mem_access(name_dict, "global_s.nested_s.nested_int2", mem_reader)[0] == [725960]

        # Pointer
        assert mem_access(name_dict, "s_ptr", mem_reader)[0] == [725440]
        assert mem_access(name_dict, "*s_ptr", mem_reader)[0] == [
            7254400,
            7254440,
            7254480,
            7254520,
            7254560,
            7254600,
        ]
        assert mem_access(name_dict, "s_ptr->an_int", mem_reader)[0] == [7254400]
        assert mem_access(name_dict, "s_ptr->an_int2", mem_reader)[0] == [7254440]

        # Namespace
        assert mem_access(name_dict, "ns::ns_int", mem_reader)[0] == [725360]
        assert mem_access(name_dict, "ns::ns_s", mem_reader)[0] == [725400]
        assert mem_access(name_dict, "ns::ns_s.global_s", mem_reader)[0] == [725400]
        assert mem_access(name_dict, "*ns::ns_s.global_s", mem_reader)[0] == [7254000]

        # Cleanup generated files
        for generated_file in generated_files:
            os.system(f"rm -f {generated_file}")

    # @unittest.skip("demonstrating skipping")
    def test_array(self):
        program_name, program_definition = "array", {
            "program_text": """
                int GLOBAL_INT_ARRAY[4] = { 1, 2, 3, 4 };
                struct S_POINT {
                    int x, y;
                };
                struct S_TYPE {
                    int local_int_array[4] = { 10, 20, 30, 40 };
                    struct S_POINT local_point_array[4] = { {1,2}, {3,4}, {5,6}, {7,8} };
                } my_s;

                int main() {
                    return 0;
                }
                """
        }
        generated_files = compile_test_cpp_program(program_name, program_definition["program_text"])
        name_dict = read_elf(file_ifc, f"{program_name}.elf")
        program_path = os.path.join(TestParseElf.output_dir, program_name)
        compile_test_cpp_program(program_path, program_definition["program_text"])
        name_dict = read_elf(file_ifc, f"{program_path}.elf")
        assert mem_access(name_dict, "GLOBAL_INT_ARRAY", mem_reader)[0] == [
            711200,
            711240,
            711280,
            711320,
        ]
        assert mem_access(name_dict, "GLOBAL_INT_ARRAY[0]", mem_reader)[0] == [711200]
        assert mem_access(name_dict, "GLOBAL_INT_ARRAY[2]", mem_reader)[0] == [711280]
        assert mem_access(name_dict, "my_s.local_int_array", mem_reader)[0] == [
            711360,
            711400,
            711440,
            711480,
        ]
        assert mem_access(name_dict, "my_s.local_int_array[2]", mem_reader)[0] == [711440]
        assert mem_access(name_dict, "my_s.local_point_array", mem_reader)[0] == [
            711520,
            711560,
            711600,
            711640,
            711680,
            711720,
            711760,
            711800,
        ]
        assert mem_access(name_dict, "my_s.local_point_array[1].x", mem_reader)[0] == [711600]
        assert mem_access(name_dict, "my_s.local_point_array[2].y", mem_reader)[0] == [711720]
        for generated_file in generated_files:
            os.system(f"rm -f {generated_file}")

    # @unittest.skip("demonstrating skipping")
    def test_double_array(self):
        program_name, program_definition = "double_array", {
            "program_text": """
                int double_int_array[2][3] = { {1,2,3}, {4,5,6} };
                int main() {
                    return 0;
                }
                """
        }
        program_path = os.path.join(TestParseElf.output_dir, program_name)
        compile_test_cpp_program(program_path, program_definition["program_text"])
        name_dict = read_elf(file_ifc, f"{program_path}.elf")
        generated_files = compile_test_cpp_program(program_name, program_definition["program_text"])
        name_dict = read_elf(file_ifc, f"{program_name}.elf")

        assert mem_access(name_dict, "double_int_array[0][2]", mem_reader)[0] == [10 * ((71120) + 2 * 4)]
        assert mem_access(name_dict, "double_int_array[1][2]", mem_reader)[0] == [10 * ((71120) + 5 * 4)]
        assert mem_access(name_dict, "double_int_array[1]", mem_reader)[0] == [
            10 * ((71120) + 3 * 4),
            10 * ((71120) + 4 * 4),
            10 * ((71120) + 5 * 4),
        ]
        assert mem_access(name_dict, "double_int_array", mem_reader)[0] == [10 * ((71120) + i * 4) for i in range(6)]

        # These are expected to throw exceptions
        with self.assertRaises(Exception):
            mem_access(name_dict, "double_int_array[1].pera", mem_reader)[0]

        for generated_file in generated_files:
            os.system(f"rm -f {generated_file}")

    def test_union(self):
        program_name, program_definition = "union", {
            "program_text": """
                struct S_TYPE {
                    int buffer, buffer2;
                    union { // unnamed union
                        int an_unnamed_int;
                        float a_unnamed_float;
                    };

                    union NAMED_UNION {
                        int an_int;
                        float a_float;
                    } my_union;
                } my_s;

                struct { // unnamed structure
                    int x;
                } my_unnamed_s;

                int main() {
                    return 0;
                }
                """
        }
        program_path = os.path.join(TestParseElf.output_dir, program_name)
        compile_test_cpp_program(program_path, program_definition["program_text"])
        elf = read_elf(file_ifc, f"{program_path}.elf")
        assert mem_access(elf, "my_s.my_union.an_int", mem_reader)[0] == [722360]
        assert mem_access(elf, "my_s.my_union.a_float", mem_reader)[0] == [722360]
        assert mem_access(elf, "my_s.an_unnamed_int", mem_reader)[0] == [722320]
        assert mem_access(elf, "my_s.a_unnamed_float", mem_reader)[0] == [722320]
        assert mem_access(elf, "my_unnamed_s.x", mem_reader)[0] == [722400]

    def test_firmware_elf(self):
        """Test finding text section in firmware elf"""
        program_name = "firmware_brisc"
        program_path = os.path.join(TestParseElf.elf_dir, program_name)
        elf = read_elf(file_ifc, f"{program_path}.elf")

        assert type(elf) == ParsedElfFile

    def test_decode_symbols(self):
        """Test decode_symbols for object files"""
        program_name = "firmware_brisc"
        program_path = os.path.join(TestParseElf.elf_dir, program_name)
        elf = read_elf(file_ifc, f"{program_path}.elf")

        assert elf.symbols["noc_reads_num_issued"] == 4289724472
        assert elf.symbols["noc_nonposted_writes_num_issued"] == 4289724464
        assert elf.symbols["noc_nonposted_writes_acked"] == 4289724456
        assert elf.symbols["noc_nonposted_atomics_acked"] == 4289724448
        assert elf.symbols["noc_posted_writes_num_issued"] == 4289724440

    def get_var_addr(self, name_dict, name):
        if name in name_dict:
            return name_dict[name]["offset"]
        else:
            return None

    def test_mem_reader(self):
        context = lib.check_context()
        for device_id in context.device_ids:
            core_loc = context.devices[device_id].get_block_locations()[0]
            mem_reader = ELF.get_mem_reader(context, device_id, core_loc)
            lib.write_words_to_device(core_loc, 0, [0x12345678, 0x90ABCDEF], device_id, context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, context) == [0x12345678, 0x90ABCDEF]
            assert mem_reader(0, 1, 1)[0] == 0x78
            assert mem_reader(1, 1, 1)[0] == 0x56
            assert mem_reader(2, 1, 1)[0] == 0x34
            assert mem_reader(3, 1, 1)[0] == 0x12
            assert mem_reader(4, 1, 1)[0] == 0xEF
            assert mem_reader(5, 1, 1)[0] == 0xCD
            assert mem_reader(6, 1, 1)[0] == 0xAB
            assert mem_reader(7, 1, 1)[0] == 0x90
            assert mem_reader(0, 2, 1)[0] == 0x5678
            assert mem_reader(2, 2, 1)[0] == 0x1234
            assert mem_reader(4, 2, 1)[0] == 0xCDEF
            assert mem_reader(6, 2, 1)[0] == 0x90AB
            assert mem_reader(0, 4, 1)[0] == 0x12345678
            assert mem_reader(4, 4, 1)[0] == 0x90ABCDEF
            assert mem_reader(0, 8, 1)[0] == 0x90ABCDEF12345678
            assert mem_reader(1, 2, 1)[0] == 0x3456
            assert mem_reader(3, 2, 1)[0] == 0xEF12
            assert mem_reader(5, 2, 1)[0] == 0xABCD
            assert mem_reader(1, 4, 1)[0] == 0xEF123456
            assert mem_reader(2, 4, 1)[0] == 0xCDEF1234
            assert mem_reader(3, 4, 1)[0] == 0xABCDEF12
            assert mem_reader(0, 8, 8) == [0x78, 0x56, 0x34, 0x12, 0xEF, 0xCD, 0xAB, 0x90]
            assert mem_reader(1, 6, 3) == [0x3456, 0xEF12, 0xABCD]


if __name__ == "__main__":
    unittest.main()
