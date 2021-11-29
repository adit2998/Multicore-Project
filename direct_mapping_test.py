cache_size = 2**7
cache_bits = 7

block_size = 2**5
block_bits = 5

cache_blocks_bits = cache_bits - block_bits
num_cache_blocks = cache_size/block_size

total_mem = 2**12
total_mem_bits = 12

# 32 byte block, thus 5 bits required
offset_bits = 5

tag_bits = total_mem_bits - (offset_bits + cache_blocks_bits)
print(tag_bits, cache_blocks_bits, offset_bits)

hex_addresses = ["070", "080", "068", "190", "084", "178", "08c", "f00", "064"]
decimals = []
for i in hex_addresses:
    decimals.append(int(i, 16))

print(decimals)

# 12 bits required so use 0:0xb where x is the total number of bits specified
bins = []
for i in decimals:
    bins.append("{0:012b}".format(i))

print(bins)

cache = {}
for i in range(int(num_cache_blocks)):
    cache[i] = [-1, -1]


for addr in bins:
    cache_line = addr[tag_bits:tag_bits+cache_blocks_bits]
    cache_line = int(cache_line, 2)

    tag = addr[:tag_bits]
    # tag = int(tag, 2)

    print(tag, cache_line)
    
    # if cache[cache_line][0] == -1  or cache[cache_line][1] != tag:
    #     print('Miss')
    # else:
    #     print('Hit')

    # Making that cache line valid
    cache[cache_line][0] = 1

    # Adding that tag into the cache line 
    # Indicating that the block of memory has been brought into the cache
    cache[cache_line][1] = tag


print(cache)
