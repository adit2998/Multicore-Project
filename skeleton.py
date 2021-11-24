# Cache block size = 64 bytes
cache_block_size = 2**6
total_block_bits = 6

# Total cache size = 32KB
total_cache_size = 2**15
total_cache_bits = 15

# Main memory size = 4Gb meaning 32bits
main_mem = 2**32
total_mem_bits = 32

# Cache block size is 64 bytes meaning 6 bits
offset_bits = 6


# Direct memory mapping
# bits required for cache set (cache line in case of direct mapping)
cache_set_bits = total_cache_bits-total_block_bits
num_cache_sets = total_cache_size/cache_block_size

# Remaining are the tag bits
tag_bits = total_mem_bits - (cache_set_bits+offset_bits)

print(tag_bits, cache_set_bits, offset_bits)
