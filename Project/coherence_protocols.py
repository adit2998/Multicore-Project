from MSI import MSI_direct_mapping, MSI_set_associative
from MESI import MESI_direct_mapping, MESI_set_associative
from MOSI import MOSI_direct_mapping, MOSI_set_associative
from MOESI import MOESI_direct_mapping, MOESI_set_associative

import math
import csv
import numpy as np
import enum
import collections


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
cache_block_bits = int(math.log(cache_block_size, 2))


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

write_method = int(input('Choose the write method:\n1. Write back\n2. Write through\n'))

num_cache_lines_per_set = int(num_cache_blocks/num_cache_sets)

total_mem = 2**32
mem_bits = int(math.log(total_mem, 2))

tag_bits = mem_bits - (cache_block_bits + cache_set_bits)

print(tag_bits, cache_set_bits, cache_block_bits)

# Read from csv file
file_name = 'insts_'+str(num_processors)+'_cores.csv'
with open(file_name, mode="r") as csvfile:
    reader = csv.reader(csvfile)
    instructions = [np.array(row).tolist() for row in reader]

class State(enum.Enum):
    Invalid = 1
    Modified = 2
    Shared = 3
    Exclusive = 4
    Owned = 5

class CacheBlock():
    def __init__(self) -> None:
        self.state = State.Invalid
        self.tag = -1

class CacheSet_Associative():
    def __init__(self) -> None:
        self.access_order = [i for i in range(num_cache_lines_per_set)]
        self.cache_blocks = [CacheBlock() for _ in range(associativity)]

class DirectoryEntry():
    def __init__(self) -> None:
        self.present = False
        self.processor_vector = [0 for _ in range(num_processors)]

Directory = collections.defaultdict(DirectoryEntry)

if mapping==1:
    cores = [[CacheBlock() for _ in range(num_cache_blocks)] for _ in range(num_processors)]
    MSI_direct_mapping(instructions, cores, Directory, tag_bits, cache_block_bits, write_method)
    MESI_direct_mapping(instructions, cores, Directory, tag_bits, cache_block_bits, write_method)
    MOSI_direct_mapping(instructions, cores, Directory, tag_bits, cache_block_bits, write_method)
    MOESI_direct_mapping(instructions, cores, Directory, tag_bits, cache_block_bits, write_method)

elif mapping==2:
    cores = [[CacheSet_Associative() for _ in range(num_cache_sets)] for _ in range(num_processors)]
    MSI_set_associative(instructions, cores, Directory, tag_bits, cache_set_bits, write_method)
    MESI_set_associative(instructions, cores, Directory, tag_bits, cache_set_bits, write_method)
    MOSI_set_associative(instructions, cores, Directory, tag_bits, cache_block_bits, write_method)
    MOESI_set_associative(instructions, cores, Directory, tag_bits, cache_block_bits, write_method)
