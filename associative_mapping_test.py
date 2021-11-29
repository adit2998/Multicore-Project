import math

cache_size = 2**7
cache_bits = 7

block_size = 2**5
block_bits = 5

# Associative cache
associativity = 2
num_cache_lines = cache_size/block_size
num_asso_cache_sets = cache_size/(block_size*associativity)
num_cache_set_bits = int(math.log(num_asso_cache_sets, 2))

cache_lines_in_set = int(num_cache_lines/num_asso_cache_sets)

total_mem = 2**12
total_mem_bits = 12

# 32 byte block, thus 5 bits required
offset_bits = 5

tag_bits = total_mem_bits - (offset_bits + num_cache_set_bits)
print(tag_bits, num_cache_set_bits, offset_bits)


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

# set_num : [LRU bit, [[-1, -1], [-1, -1]...num of cache lines per set]]
cache = {}
for i in range(int(num_asso_cache_sets)):
    cache[i] = [0, [[-1, -1] for _ in range(cache_lines_in_set)], []]

# print(cache)
# print(num_asso_cache_sets)
# print(cache_lines_in_set)



for addr in bins:

    cache_set = addr[tag_bits:tag_bits+num_cache_set_bits]
    cache_set = int(cache_set, 2)

    tag = addr[:tag_bits]    
    # tag = int(tag, 2)

    present_tag = False

    for line in cache[cache_set][1]:
        if line[1]==tag:
            present_tag = True

    if not present_tag:
        # If tag not present in cache set then it is a miss.
        # Place that tag in the least recently used position
        print('Miss')

        # Least recently used line
        lru_line = cache[cache_set][0]

        # Set valid bit to one
        cache[cache_set][1][lru_line][0] = 1
        # Set the tag 
        cache[cache_set][1][lru_line][1] = tag

        # Increment counter for least recently used bit. Mod for wrap around later
        cache[cache_set][0] = (cache[cache_set][0]+1)%cache_lines_in_set

        print('----------------------------------------------')
        print(cache)

    else:
        print('Hit')
        lru_line = cache[cache_set][0]



print(cache)