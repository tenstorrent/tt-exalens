from dbd.tt_debuda_init import init_debuda
from dbd.tt_debuda_lib import write_to_device, read_words_from_device
from dbd.tt_debuda_lib import run_elf
import sys

#buffer_A = [0x80, 0x44, 0, 0] * 256
#buffer_B = [0x40, 0x48, 0, 0] * 256

context = init_debuda()

num_bytes = write_to_device("18-18", 0x1b000, buffer_A, context=context)
num_bytes = write_to_device("18-18", 0x1c000, buffer_B, context=context)

run_elf("build/elf/eltwise_add_test_trisc0.elf", "18-18", risc_id = 1)
run_elf("build/elf/eltwise_add_test_trisc1.elf", "18-18", risc_id = 2)
run_elf("build/elf/eltwise_add_test_trisc2.elf", "18-18", risc_id = 3)

print("buffer_A")
read_data = read_words_from_device("18-18", 0x1b000, word_count = 1)
read_data = read_data[0].to_bytes(4, 'big')
read_data = list(read_data)
for i in read_data:
    print(hex(i))

print("buffer_B")
read_data = read_words_from_device("18-18", 0x1c000, word_count = 1)
read_data = read_data[0].to_bytes(4, 'big')
read_data = list(read_data)
for i in read_data:
    print(hex(i))

print("buffer_Dest")
dest_list = []
dest_buffer = read_words_from_device("18-18", 0x1a000, word_count = 4)
for data in dest_buffer:
    read_data = data.to_bytes(4, 'big')
    read_data = list(read_data)
    for i in read_data:
        dest_list.append(hex(i))
print(dest_list)

# Using temp mailbox before moving mailbox address in defines
#print("UNPACK mailbox")
#read_data = read_words_from_device("18-18", 0x19FF4, word_count = 1)
#read_data = read_data[0].to_bytes(4, 'big')
#read_data = list(read_data)
#print(read_data)
#for i in read_data:
#    print(hex(i))
#
#print("MATH mailbox")
#read_data = read_words_from_device("18-18", 0x19FF8, word_count = 1)
#read_data = read_data[0].to_bytes(4, 'big')
#read_data = list(read_data)
#print(read_data)
#for i in read_data:
#    print(hex(i))
#
#print("PACK mailbox")
#read_data = read_words_from_device("18-18", 0x19FFC, word_count = 1)
#read_data = read_data[0].to_bytes(4, 'big')
#read_data = list(read_data)
#print(read_data)
#for i in read_data:
#    print(hex(i))