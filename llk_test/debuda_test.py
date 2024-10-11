from dbd.tt_debuda_init import init_debuda
from dbd.tt_debuda_lib import write_to_device, read_words_from_device
from dbd.tt_debuda_lib import run_elf
import sys
#sys.path.append('llk_test/helpers')
#import objdump_utils

context = init_debuda()

buffer_A = [0x40] * 1024 
buffer_B = [0x40,0x48] * 512

num_bytes = write_to_device("18-18", 0x1c000, buffer_A, context=context)
num_bytes = write_to_device("18-18", 0x1b000, buffer_B, context=context)

run_elf("../build/riscv-src/wormhole/run_elf_test.trisc0.elf", "18-18", risc_id = 1)
run_elf("../build/riscv-src/wormhole/run_elf_test.trisc1.elf", "18-18", risc_id = 2)
run_elf("../build/riscv-src/wormhole/run_elf_test.trisc2.elf", "18-18", risc_id = 3)

print("buffer_A")
read_data = read_words_from_device("18-18", 0x1c000, word_count = 1)
read_data = read_data[0].to_bytes(4, 'big')
read_data = list(read_data)
for i in read_data:
    print(hex(i))

print("buffer_B")
read_data = read_words_from_device("18-18", 0x1b000, word_count = 1)
read_data = read_data[0].to_bytes(4, 'big')
read_data = list(read_data)
for i in read_data:
    print(hex(i))

print("buffer_Dest")
read_data = read_words_from_device("18-18", 0x17d50, word_count = 1)
read_data = read_data[0].to_bytes(4, 'big')
read_data = list(read_data)
for i in read_data:
    print(hex(i))

print("UNPACK mailbox")
read_data = read_words_from_device("18-18", 0x0000d004, word_count = 1)
read_data = read_data[0].to_bytes(4, 'big')
read_data = list(read_data)
for i in read_data:
    print(hex(i))

print("MATH mailbox")
read_data = read_words_from_device("18-18", 0x00012004, word_count = 1)
read_data = read_data[0].to_bytes(4, 'big')
read_data = list(read_data)
for i in read_data:
    print(hex(i))

print("PACK mailbox")
read_data = read_words_from_device("18-18", 0x00016004, word_count = 1)
read_data = read_data[0].to_bytes(4, 'big')
read_data = list(read_data)
for i in read_data:
    print(hex(i))
