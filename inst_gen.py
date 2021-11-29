import csv
import numpy as np
import random
from operator import add, sub

num_processors = 4

cache_size = 2**15
cache_bits = 15

block_size = 2**6
block_bits = 6

cache_blocks_bits = cache_bits - block_bits
num_cache_blocks = int(cache_size/block_size)

total_mem = 2**32
total_mem_bits = 32

# 64 byte block, thus 6 bits required
offset_bits = 6

tag_bits = total_mem_bits - (offset_bits + cache_blocks_bits)
print(tag_bits, cache_blocks_bits, offset_bits)

my_list = [[1,2,3], [4,5,6], [7,8,9]]


# # Write to csv file
# with open("test.csv", mode="w", newline='') as csvfile:
#     writer = csv.writer(csvfile)
#     writer.writerows(my_list)

# # Read from csv file
# with open("test.csv", mode="r") as csvfile:
#     reader = csv.reader(csvfile)
#     insts = [np.array(row, dtype=int).tolist() for row in reader]

# print(insts)

addresses = random.sample(range(0, 2**32-1), 10)
close_range = random.sample(range(0, 1000), 100)
# print(addresses)

insts = []
ops = (add, sub)

# time = 0
# # instruction = [time, processor, address, access_type, num of bytes to access]
# for i in range(len(addresses)):
#     inst = [time, random.randint(0, num_processors-1), hex(addresses[i]), random.randint(0, 1), random.randint(0, 4)]
#     instructions.append(inst)
#     time+=1

#     for j in range(len(close_range)):
#         op = random.choice(ops)
#         addr = op(addresses[i], random.choice(close_range))        
#         inst = [time, random.randint(0, num_processors-1), hex(addr), random.randint(0, 1), random.randint(0, 4)]
#         instructions.append(inst)
#         time+=1

for i in range(len(addresses)):
    insts.append(hex(addresses[i]))

    for j in range(len(close_range)):
        op = random.choice(ops)        
        insts.append(hex(op(addresses[i], random.choice(close_range))))

random.shuffle(insts)

instructions = []
time = 0
# instruction = [time, processor, address, access_type, num of bytes to access]
for i in range(len(insts)):
    instructions.append([time, random.randint(0, num_processors-1), insts[i], random.randint(0, 1), random.randint(0, 4)])

# for i in range(len(instructions)):
#     print(instructions[i])
# print(len(instructions))
    

with open("test.csv", mode="w", newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(instructions)