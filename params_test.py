import math

num_processors = int(input('Enter number of processors '))
print(num_processors)

cache_size = int(input('Choose cache size:\n1. 32 KB\n2. 64 KB\n'))
total_cache_size = 0
if cache_size==1:
    total_cache_size = 2**15
    cache_bits = int(math.log(2**15, 2))
elif cache_size==2:
    total_cache_size = 2**16
    cache_bits = int(math.log(2**16, 2))
else:
    print('Incorrect value chosen')

# cache block size fixed to 64 bytes
cache_block_size = 64
cach_block_bits = int(math.log(cache_block_size, 2))


mapping = int(input('Choose the type of mapping:\n1. Direct Mapping\n2. Associative Mapping\n'))
associativity = 1
num_cache_blocks = int(total_cache_size/cache_block_size)
if mapping==1:    
    num_cache_sets = int(total_cache_size/cache_block_size)
    cache_set_bits = int(math.log(num_cache_sets, 2))
elif mapping==2:
    associativity = int(input('Select associativity '))
    print(associativity)        
    num_cache_sets = int(total_cache_size/(cache_block_size*associativity))
    print(num_cache_sets)
    cache_set_bits = int(math.log(num_cache_sets, 2))
else:
    print('Incorrect value chosen')

num_cache_lines_per_set = int(num_cache_blocks/num_cache_sets)

total_mem = 2**32
mem_bits = int(math.log(total_mem, 2))

tag_bits = mem_bits - (cach_block_bits + cache_set_bits)

print(tag_bits, cache_set_bits, cach_block_bits)
# print(num_cache_lines_per_set)
