import enum
import random
import collections

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
print(num_cache_blocks)



# addresses = random.sample(range(10, 2**32), 5)
# print(addresses)

int_addresses = [10, 20, 804659575, 804659571, 899657846, 3034242499, 2559271293, 1510703010]
hex_addresses = [hex(i) for i in int_addresses]
bins = []
for i in int_addresses:
    bins.append("{0:032b}".format(i))

# print(bins)

# print('Tag------Cache Set')
# for addr in bins:
#     cache_set = addr[tag_bits:tag_bits+cache_blocks_bits]
#     cache_set = int(cache_set, 2)

#     tag = addr[:tag_bits]
#     tag = int(tag, 2)

#     print(tag, cache_set)
#     # print(len(tag), len(cache_set))

# print(hex_addresses)


instructions = [(0, 10, 0), (0, 20, 1), (1, 804659575, 0), (0, 804659571, 1), (1, 899657846, 0), (2, 3034242499, 0), (2, 2559271293, 1), (3, 1510703010, 1)]
# instructions = [(0, 10, 1), (0, 20, 0)]

# cache_num = [valid_bit, dirty_bit, tag]
cache = {}
for i in range(int(num_cache_blocks)):
    cache[i] = [0, 0, -1]

# print(cache)

class State(enum.Enum):
    Invalid = 1
    Modified = 2
    Shared = 3

class CacheBlock():
    def __init__(self) -> None:
        self.state = State.Invalid
        self.tag = -1

cache = [CacheBlock() for i in range(num_cache_blocks)]

# print(len(cache))
# print(cache[0].tag)

class DirectoryEntry():
    def __init__(self) -> None:
        self.present = False
        self.processor_vector = [0 for _ in range(num_processors)]


cores = [[CacheBlock() for _ in range(num_cache_blocks)] for _ in range(num_processors)]
Directory = collections.defaultdict(DirectoryEntry)

# cores[0][0].state = State.Modified
# cores[0][0].tag = 10

# For Read Miss on Invalid
# Directory[0].present = True
# cores[2][0].state = State.Modified
# cores[2][0].tag = 0

# For Write Miss on Invalid
Directory[0].present = True
Directory[0].processor_vector[1] = 1
Directory[0].processor_vector[2] = 1
cores[1][0].state = State.Shared
cores[1][0].tag = 0
cores[2][0].state = State.Shared
cores[2][0].tag = 0

print('thread, tag, cache_set, access_type')
for thread, addr, access_type in instructions:
    addr = "{0:032b}".format(addr)
    cache_set = addr[tag_bits:tag_bits+cache_blocks_bits]
    cache_set = int(cache_set, 2)

    cur_tag = addr[:tag_bits]
    cur_tag = int(cur_tag, 2)

    print(thread, cur_tag, cache_set, access_type)

    # Case: if the block that the processor is requesting is in Invalid State:
    # This is a miss from Invalid state.
    if cores[thread][cache_set].state==State.Invalid or cores[thread][cache_set].tag!=cur_tag:  
                         
        if access_type==1:
            # If this is a write miss
            print('Write miss')
            if Directory[cur_tag].present:
                # --> Go to every processor that contains a copy of this block and invalidate it
                processors = Directory[cur_tag].processor_vector
                for i in range(len(processors)):
                    if Directory[cur_tag].processor_vector[i]:

                        if cores[i][cache_set].state==State.Modified:
                            # Then do a write back to main memory before putting that block from directory in invalid state.                
                            print('Write back')

                        # The copy is invalidated in the core if it was previously in modified or shared state.
                        cores[i][cache_set].state = State.Invalid
                        print('Copy in procesor ', i, ' moved to invalid state')
                        # The processor vector in the directory is updated to reflect the invalidation
                        Directory[cur_tag].processor_vector[i] = 0                        

            else:
                # 1. If the directory does not have that block, bring it from memory
                # Make it present in the directory
                Directory[cur_tag].present = True                
                    
            # --> Change the state of that block in the current processor to modified. Also update the tag
            cores[thread][cache_set].state = State.Modified
            cores[thread][cache_set].tag = cur_tag
            print('Copy updated in core ', thread)            

            # --> Update it in the directory to reflect that the block is only now present in that one core requesting it.
            Directory[cur_tag].processor_vector[thread] = 1
            print(Directory[cur_tag].processor_vector)

        # If this is a read miss
        elif access_type==0: 
            print('Read Miss')
            # Two scenarios: 
            # 1. First, this core will check the directory if any other core has this block in its cache
            if Directory[cur_tag].present:                                
                processors = Directory[cur_tag].processor_vector
                for i in range(len(processors)):
                    if Directory[cur_tag].processor_vector[i]:   
                        if cores[i][cache_set].state==State.Modified:
                            # Then do a write back to main memory before putting that block from directory in shared state.                
                            print('Write back')

                        # Copy is moved to shared state in the core that originally contains it
                        cores[i][cache_set].state = State.Shared
                        print('Copy in procesor ', i, ' moved to shared state')
                        print(cores[i][cache_set].state)

            else:
                # If the directory does not have that block, bring it from memory
                # Make it present in the directory
                print('Copy brought in from memory')
                Directory[cur_tag].present = True
            
            # --> Update it in the current cache too
            cores[thread][cache_set].state = State.Shared
            cores[thread][cache_set].tag = cur_tag
            print('Copy updated in core ', thread)
                                     
            # --> Update it in the directory to show that it is now present in the new core requesting it
            Directory[cur_tag].processor_vector[thread] = 1
            print(Directory[cur_tag].processor_vector)

    # When processor wants to read/write a block that is in Modified state, 
    # When processor wants to read only a block that is in Shared state,
    # Do nothing
    elif (cores[thread][cache_set].state==State.Modified and cores[thread][cache_set].tag==cur_tag) or (cores[thread][cache_set].state==State.Shared and cores[thread][cache_set].tag==cur_tag and access_type==0):  
        # That block will remain in the same state
        if access_type==0:
            print('Read Hit')
        else:
            print('Write Hit')

    elif (cores[thread][cache_set].state==State.Shared and cores[thread][cache_set].tag==cur_tag and access_type==1):
        # Block is already present in the Directory. So no need to check if its present in and no need to bring it from Memory
        # Simply invalidate other copies containing that block
        print('Write hit')
        processors = Directory[cur_tag].processor_vector
        for i in range(len(processors)):
            if Directory[cur_tag].processor_vector[i]:
                if cores[i][cache_set].state==State.Modified:
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

    else:
        if access_type==0:
            print('Read Hit')
        else:
            print('Write Hit')
            

