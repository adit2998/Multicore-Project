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

cache_blocks_bits = cache_bits - block_bits
num_cache_blocks = int(cache_size/block_size)

total_mem = 2**32
total_mem_bits = 32

# 64 byte block, thus 6 bits required
offset_bits = 6

tag_bits = total_mem_bits - (offset_bits + cache_blocks_bits)

# # Read from csv file
# with open("test.csv", mode="r") as csvfile:
#     reader = csv.reader(csvfile)
#     instructions = [np.array(row).tolist() for row in reader]


class State(enum.Enum):
    Invalid = 1
    Modified = 2
    Shared = 3
    Exclusive = 4

class CacheBlock():
    def __init__(self) -> None:
        self.state = State.Invalid
        self.tag = -1

class DirectoryEntry():
    def __init__(self) -> None:
        self.present = False
        self.processor_vector = [0 for _ in range(num_processors)]

cores = [[CacheBlock() for _ in range(num_cache_blocks)] for _ in range(num_processors)]
Directory = collections.defaultdict(DirectoryEntry)

instructions = [(0, 0, 10, 1, 4)]
for time, thread, addr, access_type, access_bytes in instructions:
    addr = "{0:032b}".format(addr)
    cache_set = addr[tag_bits:tag_bits+cache_blocks_bits]
    cache_set = int(cache_set, 2)

    cur_tag = addr[:tag_bits]
    cur_tag = int(cur_tag, 2)

    time, thread, access_type, access_bytes = int(time), int(thread), int(access_type), int(access_bytes)

    print(time, thread, addr, access_type, access_bytes)

    # Case: if the block that the processor is requesting is in Invalid State:
    # This is a miss from Invalid state.
    if cores[thread][cache_set].state==State.Invalid or cores[thread][cache_set].tag!=cur_tag:  
        if access_type==1:
            # If this is a write miss
            print('Write Miss')            
            if Directory[cur_tag].present:
                # Go to every processor that contains a copy of this block and invalidate it.
                processors = Directory[cur_tag].processor_vector
                for i in range(len(processors)):
                    if Directory[cur_tag].processor_vector[i]:
                        if cores[i][cache_set].state==State.Modified:
                            # If the block was in modified state
                            # Then do a write back to main memory before putting that block from directory in invalid state. (Flush)                
                            print('Write back')
                        
                        # The copy is invalidated in the core if it was previously in modified, shared, or exclusive state.
                        cores[i][cache_set].state = State.Invalid
                        print('Copy in procesor ', i, ' moved to invalid state')
                        # The processor vector in the directory is updated to reflect the invalidation
                        Directory[cur_tag].processor_vector[i] = 0  
                

            else:
                # If the directory does not have that block, bring it from memory.
                Directory[cur_tag].present = True 

            # --> Change the state of that block in the current processor to modified. Also update the tag
            cores[thread][cache_set].state = State.Modified
            cores[thread][cache_set].tag = cur_tag
            print('Copy updated in core ', thread)            

            # --> Update it in the directory to reflect that the block is only now present in that one core requesting it.
            Directory[cur_tag].processor_vector[thread] = 1
            print(Directory[cur_tag].processor_vector)

        
        elif access_type==0:            
            # This is a read miss
            print('Read Miss')
            # Either some core contains the same cache line - Then put this cache line in the requesting core in shared state.
            # Or no core contains that cache line and hence needs to brought in from memory - Then put this cache line in exclusive state.

            only_copy = True
            if Directory[cur_tag].present:
                # Means it has been previously brought in from memory. But check if other processors contain that copy.
                processors = Directory[cur_tag].processor_vector
                for i in range(len(processors)):
                    # If this cache line is present in another core, then it wont be the only copy.
                    if Directory[cur_tag].processor_vector[i]: 
                        if cores[i][cache_set].state==State.Modified:
                            # Then do a write back to main memory before putting that block from directory in shared state.                
                            print('Write back')
                            print('Cache-to-Cache Flush')

                        # Indicate there are other copies holding that block
                        only_copy = False
                        # If that copy was previously in modified or exclusive state, then move it to shared state.
                        # If that copy was previously in shared state, then it will stay in shared state.
                        cores[i][cache_set].state = State.Shared
                        print('Copy in procesor ', i, ' moved to shared state')
                        print(cores[i][cache_set].state)

            else:
                # If the directory does not have that block, bring it in from memory
                # Make it present in the directory.
                print('Copy brought in from memory')
                Directory[cur_tag].present = True

            if not only_copy:
                # If there are other cores holding a copy of that cache line, then put that block in shared state. 
                cores[thread][cache_set].state = State.Shared
            else:
                # If there are no other cores holding a copy of that cache line, then put that block in exclusive state.
                cores[thread][cache_set].state = State.Exclusive

            # --> Update it in the directory to show that it is now present in the new core requesting it
            Directory[cur_tag].processor_vector[thread] = 1
            print(Directory[cur_tag].processor_vector)


    # When processor wants to read/write a block that is in Modified state, 
    # When processor wants to read only a block that is in Shared or Exclusive state,
    # Do nothing
    elif (cores[thread][cache_set].state==State.Modified and cores[thread][cache_set].tag==cur_tag) or (cores[thread][cache_set].state==State.Shared and cores[thread][cache_set].tag==cur_tag and access_type==0) or (cores[thread][cache_set].state==State.Exclusive and cores[thread][cache_set].tag==cur_tag and access_type==0):  
        if access_type==0:
            print('Read Hit')
        else:
            print('Write Hit')


    # If the block is in shared state and there is a processor write, invalidate all other copies containing that copy of the block
    elif (cores[thread][cache_set].state==State.Shared and cores[thread][cache_set].tag==cur_tag and access_type==1):
        # Block is already present in the Directory. So no need to check if its present in and no need to bring it from Memory
        # Simply invalidate other copies containing that block
        print('Write hit')
        processors = Directory[cur_tag].processor_vector
        for i in range(len(processors)):
            if Directory[cur_tag].processor_vector[i]:
                if cores[i][cache_set].state==State.Modified:
                    # If block is in modified state, then write back
                    # Then do a write back to main memory before putting that block from directory in shared state.                
                    print('Write back')

                cores[i][cache_set].state = State.Invalid
                print('Copy in procesor ', i, ' moved to invalid state')
                Directory[cur_tag].processor_vector[i] = 0
        
        cores[thread][cache_set].state = State.Modified 
        cores[thread][cache_set].tag = cur_tag
        print('Copy updated in core ', thread)  

        # --> Update it in the directory to reflect that the block is only now present in that one core requesting it.
        Directory[cur_tag].processor_vector[thread] = 1
        print(Directory[cur_tag].processor_vector)

    elif (cores[thread][cache_set].state==State.Exclusive and cores[thread][cache_set].tag==cur_tag and access_type==1):
        # If there is a write on a cache block that is in exclusive state, 
        # Then simply put it in modified state
        # No need for invalidation since it is the only copy
        cores[thread][cache_set].state = State.Modified 
        cores[thread][cache_set].tag = cur_tag
        print('Copy updated in core ', thread)  

        # --> Update it in the directory to reflect that the block is only now present in that one core requesting it.
        Directory[cur_tag].processor_vector[thread] = 1
        print(Directory[cur_tag].processor_vector)
    
    else:
        if access_type==0:
            print('Read Hit')
        else:
            print('Write Hit')