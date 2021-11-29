import enum

class State(enum.Enum):
    Invalid = 1
    Modified = 2
    Shared = 3

class CacheBlock():
    def __init__(self) -> None:
        self.state = State.Invalid
        self.tag = -1

cache = [CacheBlock() for i in range(10)]
# cache[0].state = 'Valid'
print(cache[0].state)


num_processors = 4
class DirectoryEntry():
    def __init__(self) -> None:
        self.present = False
        self.processor_vector = [0 for i in range(num_processors)]


# Directory = {}

# Directory[10] = DirectoryEntry(10)
# print(Directory[10].processor_vector)


cores = [[CacheBlock() for _ in range(10)] for _ in range(4)]
print(cores[0][0].state)

if -1==cores[0][5].tag:
    print('Hit')

import collections
Directory = collections.defaultdict(DirectoryEntry)

print(Directory[10].present)
if 10 in Directory:
    print(True)

import csv
import numpy as np

with open("test.csv", mode="r") as csvfile:
    reader = csv.reader(csvfile)
    instructions = [np.array(row).tolist() for row in reader]

print(instructions)

for time, thread, addr, access_type, access_bytes in instructions:
    time = int(time)
    thread = int(thread)
    access_type = int(access_type)

    print(thread, access_type)
