from dbd.tt_debuda_init import init_debuda
from dbd.tt_debuda_lib import write_to_device, read_words_from_device
from dbd.tt_debuda_lib import run_elf
import sys
#sys.path.append('llk_test/helpers')
#import objdump_utils

context = init_debuda()

run_elf("build/elf/eltwise_add_test_trisc0.elf", "18-18", risc_id = 1)
run_elf("build/elf/eltwise_add_test_trisc1.elf", "18-18", risc_id = 2)
run_elf("build/elf/eltwise_add_test_trisc2.elf", "18-18", risc_id = 3)

print("buffer_A")
read_data = read_words_from_device("18-18", 0x1b000, word_count = 8)
read_data = read_data[0].to_bytes(4, 'big')
read_data = list(read_data)
for i in read_data:
    print(hex(i))

print("buffer_B")
read_data = read_words_from_device("18-18", 0x1c000, word_count = 8)
read_data = read_data[0].to_bytes(4, 'big')
read_data = list(read_data)
for i in read_data:
    print(hex(i))
