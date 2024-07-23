# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
import os

from dbd.tt_parse_elf import read_elf, mem_access
from dbd import tt_util as util



class TestFileIfc:
    def get_binary(self, filename):
        return open(filename, "rb")

file_ifc = TestFileIfc()

def compile_test_cpp_program(program_path, program_text):
    """
    Just compile a program to get an ELF file
    """
    print(f"\nCompiling {program_path}...")
    # Run ./third_party/sfpi/compiler/bin/riscv32-unknown-elf-g++ -g ./test-elf.c -o test-elf on the program_text
    import os

    elf_file_name = f"{program_path}.elf"
    src_file_name = f"{program_path}.cpp"
    os.system(f"rm -f {elf_file_name}")
    with open(f"{src_file_name}", "w") as f:
        f.write(program_text)
    os.system(
        f"{os.environ.get("DEBUDA_HOME")}/third_party/sfpi/compiler/bin/riscv32-unknown-elf-g++ -g {src_file_name} -o {program_path}.elf"
    )
    if not os.path.exists(elf_file_name):
        util.ERROR(f"ERROR: Failed to compile {src_file_name}")
        exit(1)

    return [ elf_file_name, src_file_name ]

def mem_reader(addr, size_bytes):
    """
    A simple memory reader stub that returns addr*10 for all reads. Only for testing.
    """
    word_array = []
    for i in range((size_bytes - 1) // 4 + 1):
        value_at_addr = (addr + 4 * i) * 10
        word_array.append(value_at_addr)
    # print(
    #     f"Read {size_bytes} bytes from {addr}: {', '.join([ str(x) for x in word_array])}"
    # )
    return word_array


class TestParseElf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("DEBUDA_PATH"):
            cls.output_dir = os.path.join(
                os.environ["DEBUDA_PATH"], "build", "test", "assets"
            )
        else:
            cls.output_dir = os.path.join(
                "build", "test", "assets"
            )
        cls.output_dir = os.path.abspath(cls.output_dir)

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
        assert mem_access(name_dict, "GLOBAL_INT", mem_reader)[0] == [724920]
        with self.assertRaises(Exception):
            assert mem_access(name_dict, "*GLOBAL_INT", mem_reader)[0] == [0]
        assert mem_access(name_dict, "GLOBAL_INT_PTR", mem_reader)[0] == [724960]
        assert mem_access(name_dict, "GLOBAL_INT_PTR_PTR", mem_reader)[0] == [725000]
        assert mem_access(name_dict, "*GLOBAL_INT_PTR_PTR", mem_reader)[0] == [7250000]
        assert mem_access(name_dict, "**GLOBAL_INT_PTR_PTR", mem_reader)[0] == [
            72500000
        ]
        with self.assertRaises(Exception):
            assert mem_access(name_dict, "***GLOBAL_INT_PTR_PTR", mem_reader)[
                0
            ]  # This fails
        assert mem_access(name_dict, "*s_ptr", mem_reader)[0] == [
            7252000,
            7252040,
            7252080,
            7252120,
            7252160,
            7252200,
        ]
        assert mem_access(name_dict, "GLOBAL_INT_REF", mem_reader)[0] == [7248000]
        assert mem_access(name_dict, "global_s", mem_reader)[0] == [
            725520,
            725560,
            725600,
            725640,
            725680,
            725720,
        ]
        assert mem_access(name_dict, "global_s.an_int", mem_reader)[0] == [725520]
        assert mem_access(name_dict, "global_s.an_int2", mem_reader)[0] == [725560]
        assert mem_access(name_dict, "*global_s.an_int_ptr", mem_reader)[0] == [7256000]
        assert mem_access(name_dict, "global_s.nested_s", mem_reader)[0] == [
            725680,
            725720,
        ]
        assert mem_access(name_dict, "global_s.nested_s.nested_int", mem_reader)[0] == [
            725680
        ]
        assert mem_access(name_dict, "global_s.nested_s.nested_int2", mem_reader)[
            0
        ] == [725720]

        # Pointer
        assert mem_access(name_dict, "s_ptr", mem_reader)[0] == [725200]
        assert mem_access(name_dict, "*s_ptr", mem_reader)[0] == [
            7252000,
            7252040,
            7252080,
            7252120,
            7252160,
            7252200,
        ]
        assert mem_access(name_dict, "s_ptr->an_int", mem_reader)[0] == [7252000]
        assert mem_access(name_dict, "s_ptr->an_int2", mem_reader)[0] == [7252040]

        # Namespace
        assert mem_access(name_dict, "ns::ns_int", mem_reader)[0] == [725120]
        assert mem_access(name_dict, "ns::ns_s", mem_reader)[0] == [725160]
        assert mem_access(name_dict, "ns::ns_s.global_s", mem_reader)[0] == [725160]
        assert mem_access(name_dict, "*ns::ns_s.global_s", mem_reader)[0] == [7251600]

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
            710960,
            711000,
            711040,
            711080,
        ]
        assert mem_access(name_dict, "GLOBAL_INT_ARRAY[0]", mem_reader)[0] == [710960]
        assert mem_access(name_dict, "GLOBAL_INT_ARRAY[2]", mem_reader)[0] == [711040]
        assert mem_access(name_dict, "my_s.local_int_array", mem_reader)[0] == [
            711120,
            711160,
            711200,
            711240,
        ]
        assert mem_access(name_dict, "my_s.local_int_array[2]", mem_reader)[0] == [
            711200
        ]
        assert mem_access(name_dict, "my_s.local_point_array", mem_reader)[0] == [
            711280,
            711320,
            711360,
            711400,
            711440,
            711480,
            711520,
            711560,
        ]
        assert mem_access(name_dict, "my_s.local_point_array[1].x", mem_reader)[0] == [
            711360
        ]
        assert mem_access(name_dict, "my_s.local_point_array[2].y", mem_reader)[0] == [
            711480
        ]
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

        assert mem_access(name_dict, "double_int_array[0][2]", mem_reader)[0] == [
            10 * ((71096) + 2 * 4)
        ]
        assert mem_access(name_dict, "double_int_array[1][2]", mem_reader)[0] == [
            10 * ((71096) + 5 * 4)
        ]
        assert mem_access(name_dict, "double_int_array[1]", mem_reader)[0] == [
            10 * ((71096) + 3 * 4),
            10 * ((71096) + 4 * 4),
            10 * ((71096) + 5 * 4),
        ]
        assert mem_access(name_dict, "double_int_array", mem_reader)[0] == [
            10 * ((71096) + i * 4) for i in range(6)
        ]

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
        name_dict = read_elf(file_ifc, f"{program_path}.elf")
        assert mem_access(name_dict, "my_s.my_union.an_int", mem_reader)[0] == [722120]
        assert mem_access(name_dict, "my_s.my_union.a_float", mem_reader)[0] == [722120]
        assert mem_access(name_dict, "my_s.an_unnamed_int", mem_reader)[0] == [722080]
        assert mem_access(name_dict, "my_s.a_unnamed_float", mem_reader)[0] == [722080]
        assert mem_access(name_dict, "my_unnamed_s.x", mem_reader)[0] == [722160]

    def get_var_addr(self, name_dict, name):
        if name in name_dict:
            return name_dict[name]["offset"]
        else:
            return None

    @unittest.skip("TODO: This should be run in Buda repo (issue #11).")
    def test_brisc(self):
        name_dict = read_elf(file_ifc, "./debuda_test/brisc/brisc.elf")
        epoch_id_addr = self.get_var_addr(name_dict, "EPOCH_INFO_PTR->epoch_id")


if __name__ == "__main__":
    unittest.main()
