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

num_cache_blocks = cache_size/block_size

cache_set_bits = cache_bits - (block_bits+associativity_bits)
num_cache_sets = int(cache_size/(block_size*associativity))

num_cache_lines_per_set = int(num_cache_blocks/num_cache_sets)

total_mem = 2**32
total_mem_bits = 32

# 64 byte block, thus 6 bits required
offset_bits = 6

tag_bits = total_mem_bits - (offset_bits + cache_set_bits)

print(tag_bits, cache_set_bits, offset_bits)
print(num_cache_lines_per_set)

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
        self.access_order = [i for i in range(num_cache_lines_per_set)]
        self.cache_blocks = [CacheBlock() for _ in range(associativity)]

class DirectoryEntry():
    def __init__(self) -> None:
        self.present = False
        self.processor_vector = [0 for _ in range(num_processors)]

cores = [[CacheSet() for _ in range(num_cache_sets)] for _ in range(num_processors)]
Directory = collections.defaultdict(DirectoryEntry)

# print(cores[0][0].cache_blocks[0].state)
print(cores[0][0].access_order)

# Directory[0].processor_vector[0] = 1
# Directory[0].processor_vector[1] = 1
# Directory[0].present = True

# cores[1][0].cache_blocks[0].tag = 0
# cores[1][0].cache_blocks[0].state = State.Modified

instructions = [(0, 0, 10, 1, 4)]
for time, thread, addr, access_type, access_bytes in instructions:
    addr = "{0:032b}".format(addr)
    cache_set = addr[tag_bits:tag_bits+cache_set_bits]
    cache_set = int(cache_set, 2)

    cur_tag = addr[:tag_bits]
    cur_tag = int(cur_tag, 2)

    time, thread, access_type, access_bytes = int(time), int(thread), int(access_type), int(access_bytes)

    print(time, thread, addr, access_type, access_bytes)
    # print(len(cache_set))
    # print(len(cur_tag))

    # Check if a cache block in the set contains that tag.
    # If no cache block contains that tag, then it is a miss on invalid 
    core_cache_blocks = cores[thread][cache_set].cache_blocks
    tag_present = False
    tag_state = State.Invalid
    for i in range(len(core_cache_blocks)):
        if core_cache_blocks[i].tag==cur_tag and core_cache_blocks[i].state!=State.Invalid:
            # Meaning the tag is present in the block of that cache set and is valid
            tag_present = True
            # Save the state of that tag in var tag_state
            tag_state = core_cache_blocks[i].state

            # Update access order if it is a hit
            cores[thread][cache_set].access_order.remove(i)
            cores[thread][cache_set].access_order.append(i)

    # print(cores[thread][cache_set].cache_blocks[0].state)

    if not tag_present:
        if access_type==1:
            # Write miss on invalid
            print('Write Miss')
            
            # 1. First, this core will check the directory if any other core has this block in its cache
            if Directory[cur_tag].present:
                # Go to every other processor that contains this copy and invalidate it
                processors = Directory[cur_tag].processor_vector
                for i in range(len(processors)):
                    if Directory[cur_tag].processor_vector[i]:  
                        # If a core has that tag in its cache set,
                        # Then go to every cache block associated with that set and find the tag before invalidating it. 
                        core_cache_blocks = cores[i][cache_set].cache_blocks
                        for j in range(len(core_cache_blocks)):

                            if cores[i][cache_set].cache_blocks[j].tag==cur_tag:
                                # If that tag value is present in any of the cache blocks of that set.
                                if cores[i][cache_set].cache_blocks[j].state==State.Modified:
                                    # Then do a write back to main memory before putting that block from directory in shared state.                
                                    print('Write back')

                                cores[i][cache_set].cache_blocks[j].state==State.Invalid
                                print('Copy in procesor ', i, ' in cache set ',cache_set, ' and cache block ', j, ' moved to invalid state')
                                # Update the least recently used list for the cache_blocks of that set.
                                cores[i][cache_set].access_order.remove(j)
                                cores[i][cache_set].access_order.append(j)

            else:
                # If the directory does not have that block, bring it from memory
                # Make it present in the directory
                print('Copy brought in from memory')
                Directory[cur_tag].present = True

            # --> Update it in the current cache too
            target_block = cores[thread][cache_set].access_order.pop(0)
            print(target_block)
            cores[thread][cache_set].cache_blocks[target_block].state = State.Modified
            cores[thread][cache_set].cache_blocks[target_block].tag = cur_tag
            print('Copy updated in core ', thread, ' moved to modified state')
            # Update the access order of that cache set too            
            cores[thread][cache_set].access_order.append(target_block)

            # --> Update it in the directory to show that it is now present in the new core requesting it
            Directory[cur_tag].processor_vector[thread] = 1
            print(Directory[cur_tag].processor_vector)



        elif access_type==0:
            # Read miss on invalid
            print('Read Miss')

            # 1. First, this core will check the directory if any other core has this block in its cache
            if Directory[cur_tag].present:     
                processors = Directory[cur_tag].processor_vector
                for i in range(len(processors)):
                    if Directory[cur_tag].processor_vector[i]:  
                        # If a core has that tag in its cache set,
                        # Then go to every cache block associated with that set and find the tag before moving it to shared state. 
                        core_cache_blocks = cores[i][cache_set].cache_blocks
                        for j in range(len(core_cache_blocks)):

                            if cores[i][cache_set].cache_blocks[j].tag==cur_tag:
                                # If that tag value is present in any of the cache blocks of that set.
                                if cores[i][cache_set].cache_blocks[j].state==State.Modified:
                                    # Then do a write back to main memory before putting that block from directory in shared state.                
                                    print('Write back')

                                cores[i][cache_set].cache_blocks[j].state==State.Shared
                                print('Copy in procesor ', i, ' in cache set ',cache_set, ' and cache block ', j, ' moved to shared state')
                                # Update the least recently used list for the cache_blocks of that set.
                                cores[i][cache_set].access_order.remove(j)
                                cores[i][cache_set].access_order.append(j)
                                # The processor vector in the directory is updated to reflect the invalidation
                                Directory[cur_tag].processor_vector[i] = 0

            else:
                # If the directory does not have that block, bring it from memory
                # Make it present in the directory
                print('Copy brought in from memory')
                Directory[cur_tag].present = True

            # --> Update it in the current cache too
            target_block = cores[thread][cache_set].access_order.pop(0)
            print(target_block)
            cores[thread][cache_set].cache_blocks[target_block].state = State.Shared
            cores[thread][cache_set].cache_blocks[target_block].tag = cur_tag
            print('Copy updated in core ', thread, ' moved to shared state')
            # Update the access order of that cache set too            
            cores[thread][cache_set].access_order.append(target_block)

            # --> Update it in the directory to show that it is now present in the new core requesting it
            Directory[cur_tag].processor_vector[thread] = 1
            print(Directory[cur_tag].processor_vector)
    

    elif (tag_present and tag_state==State.Modified) or (tag_present and tag_state==State.Shared and access_type==0):
        # Do nothing. Keep the same state but update the access order
        if access_type==0:
            print('Read Hit')
        else:
            print('Write Hit')        


    elif (tag_present and access_type==1 and tag_state==State.Shared):
        print('Write hit')

        # Block is already present in the Directory. So no need to check if its present in and no need to bring it from Memory
        # Simply invalidate other copies containing that block   
        # Go to every other processor that contains this copy and invalidate it
        processors = Directory[cur_tag].processor_vector
        for i in range(len(processors)):
            if Directory[cur_tag].processor_vector[i]:  
                # If a core has that tag in its cache set,
                # Then go to every cache block associated with that set and find the tag before invalidating it. 
                core_cache_blocks = cores[i][cache_set].cache_blocks
                for j in range(len(core_cache_blocks)):

                    if cores[i][cache_set].cache_blocks[j].tag==cur_tag:
                        # If that tag value is present in any of the cache blocks of that set.
                        if cores[i][cache_set].cache_blocks[j].state==State.Modified:
                            # Then do a write back to main memory before putting that block from directory in shared state.                
                            print('Write back')

                        cores[i][cache_set].cache_blocks[j].state==State.Invalid
                        print('Copy in procesor ', i, ' in cache set ',cache_set, ' and cache block ', j, ' moved to invalid state')
                        # Update the least recently used list for the cache_blocks of that set.
                        cores[i][cache_set].access_order.remove(j)
                        cores[i][cache_set].access_order.append(j)    
                        # The processor vector in the directory is updated to reflect the invalidation
                        Directory[cur_tag].processor_vector[i] = 0

        # --> Update it in the current cache too
        target_block = cores[thread][cache_set].access_order.pop(0)
        print(target_block)
        cores[thread][cache_set].cache_blocks[target_block].state = State.Modified
        cores[thread][cache_set].cache_blocks[target_block].tag = cur_tag
        print('Copy updated in core ', thread, ' moved to modified state')
        # Update the access order of that cache set too            
        cores[thread][cache_set].access_order.append(target_block)

        # --> Update it in the directory to show that it is now present in the new core requesting it
        Directory[cur_tag].processor_vector[thread] = 1
        print(Directory[cur_tag].processor_vector) 



    else:
        # Update access orders too
        if access_type==0:
            print('Read Hit')
        else:
            print('Write Hit')