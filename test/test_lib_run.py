from dbd import tt_debuda_init
from dbd import tt_debuda_lib

try:
	context = tt_debuda_init.init_debuda()
except:
	exit(1)
	
# Write to L1 cache
tt_debuda_lib.write_to_device("1,1", 0x100, [122, 200], context=context)

# Read from L1 cache
data = tt_debuda_lib.read_words_from_device("1,1", 0x100, word_count=2, context=context)

print(data)