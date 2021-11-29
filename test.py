import enum
import random
import collections
import csv
import numpy as np


num_processors = 4

cache_size = 2**15
cache_bits = 15

block_size = 2**6
block_bits = 6

associativity = 2**2
associativity_bits = 2

cache_set_bits = cache_bits - (block_bits+associativity_bits)
num_cache_sets = int(cache_size/(block_size*associativity))

total_mem = 2**32
total_mem_bits = 32

# 64 byte block, thus 6 bits required
offset_bits = 6

tag_bits = total_mem_bits - (offset_bits + cache_set_bits)

print(tag_bits, cache_set_bits, offset_bits)

class State(enum.Enum):
    Invalid = 1
    Modified = 2
    Shared = 3


class CacheBlock():
    def __init__(self) -> None:
        self.state = State.Invalid
        self.tag = -1

class CacheSet():
    def __init__(self) -> None:
        self.access_order = []
        self.cache_blocks = [CacheBlock() for _ in range(associativity)]

class DirectoryEntry():
    def __init__(self) -> None:
        self.present = False
        self.processor_vector = [0 for _ in range(num_processors)]

cores = [[CacheSet() for _ in range(num_cache_sets)] for _ in range(num_processors)]

# print(cores[0][0].cache_blocks[0].state)
print(cores[0][0].access_order)