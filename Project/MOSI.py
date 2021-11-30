import enum
from os import read

from Summary import printSummary

class State(enum.Enum):
    Invalid = 1
    Modified = 2
    Shared = 3
    Owned = 4

def MOSI_direct_mapping(instructions, cores, Directory, tag_bits, cache_blocks_bits, write_method):
    print('MOSI Protocol with Direct Mapping')
    read_misses, write_misses, read_hits, write_hits, invalidations, write_backs, directory_transfers = 0, 0, 0, 0, 0, 0, 0

    for time, thread, addr, access_type, access_bytes in instructions:
        addr = "{0:032b}".format(int(addr, 16))
        cache_set = addr[tag_bits:tag_bits+cache_blocks_bits]
        cache_set = int(cache_set, 2)

        cur_tag = addr[:tag_bits]
        cur_tag = int(cur_tag, 2)

        time, thread, access_type, access_bytes = int(time), int(thread), int(access_type), int(access_bytes)        

        if cores[thread][cache_set].state==State.Invalid or cores[thread][cache_set].tag!=cur_tag:  
            if access_type==1:
                # print('Write Miss')
                write_misses += 1
                if Directory[cur_tag].present:
                    # --> Go to every processor that contains a copy of this block and invalidate it
                    processors = Directory[cur_tag].processor_vector
                    for i in range(len(processors)):
                        if Directory[cur_tag].processor_vector[i]:

                            if cores[i][cache_set].state==State.Modified:
                                # Then do a write back to main memory before putting that block from directory in invalid state.                
                                # print('Write back')
                                write_backs += 1

                            # if cores[i][cache_set].state==State.Owned:                                          
                            #     print('Cache-to-Cache Flush')
                            directory_transfers += 1
                            invalidations += 1
                            # The copy is invalidated in the core if it was previously in modified, shared or owned state.
                            cores[i][cache_set].state = State.Invalid
                            # print('Copy in procesor ', i, ' moved to invalid state')
                            # The processor vector in the directory is updated to reflect the invalidation
                            Directory[cur_tag].processor_vector[i] = 0   
                
                else:
                    # If the directory does not have that block, bring it from memory
                    # Make it present in the directory
                    # print('Copy brought in from memory')
                    Directory[cur_tag].present = True

                # --> Change the state of that block in the current processor to modified. Also update the tag
                cores[thread][cache_set].state = State.Modified
                cores[thread][cache_set].tag = cur_tag
                # print('Copy updated in core ', thread)            

                # --> Update it in the directory to reflect that the block is only now present in that one core requesting it.
                Directory[cur_tag].processor_vector[thread] = 1
                # print(Directory[cur_tag].processor_vector)


            elif access_type==0:
                # print('Read Miss')
                read_misses += 1
                # Either some core contains that block or it needs to be brought in from main memory
                if Directory[cur_tag].present:
                    # Means it has been previously brought in from main memory.
                    processors = Directory[cur_tag].processor_vector
                    for i in range(len(processors)):
                        # If this cache line is present in another core, then it wont be the only copy.
                        if Directory[cur_tag].processor_vector[i]: 
                            directory_transfers += 1

                            if cores[i][cache_set].state==State.Modified:
                                # If a core contains that block in modified state, then put it in owned state
                                # Also flush out the value (cache to cache transfer)
                                # Meaning the core containing the block in modified state will give out the value to the requesting core, 
                                # but will maintain ownership of that block
                                cores[i][cache_set].state = State.Owned
                                # print('Cache-to-Cache Flush')

                            # elif cores[i][cache_set].state==State.Owned:
                            #     # If the core containing the block is already in owned state,
                            #     # It will just flush out the value to the requesting core.
                            #     print('Cache-to-Cache Flush')                            

                else:
                    # If the directory does not have that block, bring it from memory
                    # Make it present in the directory
                    # print('Copy brought in from memory')
                    Directory[cur_tag].present = True
                
                # --> Update it in the current cache too
                cores[thread][cache_set].state = State.Shared
                cores[thread][cache_set].tag = cur_tag
                # print('Copy updated in core ', thread)
                                        
                # --> Update it in the directory to show that it is now present in the new core requesting it
                Directory[cur_tag].processor_vector[thread] = 1
                # print(Directory[cur_tag].processor_vector)


        elif (cores[thread][cache_set].state==State.Modified and cores[thread][cache_set].tag==cur_tag) or (cores[thread][cache_set].state==State.Shared and cores[thread][cache_set].tag==cur_tag and access_type==0) or (cores[thread][cache_set].state==State.Owned and cores[thread][cache_set].tag==cur_tag and access_type==0):
            # That block will remain in the same state
            if access_type==0:
                # print('Read Hit')
                read_hits += 1
            else:
                # print('Write Hit') 
                if write_method==2:
                    write_backs += 1
                write_hits += 1

        elif (cores[thread][cache_set].state==State.Owned and cores[thread][cache_set].tag==cur_tag and access_type==1):
            # Simply invalidate other copies containing that block
            # print('Write hit')
            if write_method==2:
                write_backs += 1

            write_hits += 1
            processors = Directory[cur_tag].processor_vector
            for i in range(len(processors)):
                if Directory[cur_tag].processor_vector[i]:
                    if cores[i][cache_set].state==State.Modified:
                        # If block is in modified state, then write back
                        # Then do a write back to main memory before putting that block from directory in shared state.                
                        # print('Write back')
                        write_backs += 1

                    # Put the cache block in invalid state if it is in modified or owned state.
                    cores[i][cache_set].state = State.Invalid
                    directory_transfers += 1
                    invalidations += 1
                    # print('Copy in procesor ', i, ' moved to invalid state')
                    Directory[cur_tag].processor_vector[i] = 0
            
            cores[thread][cache_set].state = State.Modified 
            cores[thread][cache_set].tag = cur_tag
            # print('Copy updated in core ', thread)  

            # --> Update it in the directory to reflect that the block is only now present in that one core requesting it.
            Directory[cur_tag].processor_vector[thread] = 1
            # print(Directory[cur_tag].processor_vector)

        
        elif (cores[thread][cache_set].state==State.Shared and cores[thread][cache_set].tag==cur_tag and access_type==1):
            # Invalidate other copies containing that block. 
            if write_method==2:
                write_backs += 1

            write_hits += 1

            processors = Directory[cur_tag].processor_vector
            for i in range(len(processors)):
                if Directory[cur_tag].processor_vector[i]:                
                    # This block cannot be in modified or owned state in any other core. Hence only consider shared state
                    if cores[i][cache_set].state==State.Modified:
                        # If block is in modified state, then write back
                        # Then do a write back to main memory before putting that block from directory in shared state.                
                        # print('Write back')
                        write_backs += 1
                        
                    # Put the cache block in invalid state if it is in shared state.
                    cores[i][cache_set].state = State.Invalid
                    invalidations += 1
                    directory_transfers += 1
                    # print('Copy in procesor ', i, ' moved to invalid state')
                    Directory[cur_tag].processor_vector[i] = 0

            # Update state of block from invalid to modified. 
            cores[thread][cache_set].state = State.Modified 
            cores[thread][cache_set].tag = cur_tag
            # print('Copy updated in core ', thread)  

            # --> Update it in the directory to reflect that the block is only now present in that one core requesting it.
            Directory[cur_tag].processor_vector[thread] = 1            

    printSummary(read_misses, write_misses, read_hits, write_hits, invalidations, write_backs, directory_transfers)

def MOSI_set_associative(instructions, cores, Directory, tag_bits, cache_set_bits, write_method):
    print('MOSI Protocol with Set-Associative mapping')

    read_misses, write_misses, read_hits, write_hits, invalidations, write_backs, directory_transfers = 0, 0, 0, 0, 0, 0, 0

    for time, thread, addr, access_type, access_bytes in instructions:
        addr = "{0:032b}".format(int(addr, 16))
        cache_set = addr[tag_bits:tag_bits+cache_set_bits]
        cache_set = int(cache_set, 2)

        cur_tag = addr[:tag_bits]
        cur_tag = int(cur_tag, 2)

        time, thread, access_type, access_bytes = int(time), int(thread), int(access_type), int(access_bytes)        

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

        if not tag_present:
            if access_type==1:
                # print('Write Miss')
                write_misses += 1

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
                                        # print('Write back')
                                        write_backs += 1

                                    # elif cores[i][cache_set].cache_blocks[j].state==State.Owned:
                                    #     print('Cache-to-Cache Flush')

                                    # Any other core containing a copy of that block is moved to invalid state from modified, shared or owned state
                                    cores[i][cache_set].cache_blocks[j].state==State.Invalid
                                    invalidations += 1
                                    directory_transfers += 1
                                    # print('Copy in procesor ', i, ' in cache set ',cache_set, ' and cache block ', j, ' moved to invalid state')
                                    # Update the least recently used list for the cache_blocks of that set.
                                    cores[i][cache_set].access_order.remove(j)
                                    cores[i][cache_set].access_order.append(j)

                                    # The processor vector in the directory is updated to reflect the invalidation
                                    Directory[cur_tag].processor_vector[i] = 0

                else:
                    # If the directory does not have that block, bring it from memory
                    # Make it present in the directory
                    # print('Copy brought in from memory')
                    Directory[cur_tag].present = True

                # --> Update it in the current cache too
                target_block = cores[thread][cache_set].access_order.pop(0)                
                cores[thread][cache_set].cache_blocks[target_block].state = State.Modified
                cores[thread][cache_set].cache_blocks[target_block].tag = cur_tag
                # print('Copy updated in core ', thread, ' moved to modified state')
                # Update the access order of that cache set too            
                cores[thread][cache_set].access_order.append(target_block)

                # --> Update it in the directory to show that it is now present in the new core requesting it
                Directory[cur_tag].processor_vector[thread] = 1                

            elif access_type==0:
                read_misses += 1
                # print('Read Miss')

                if Directory[cur_tag].present: 
                    processors = Directory[cur_tag].processor_vector
                    for i in range(len(processors)):

                        if Directory[cur_tag].processor_vector[i]:  
                            # If a core has that tag in its cache set,
                            # Then go to every cache block associated with that set and find the tag before moving it to shared state. 
                            core_cache_blocks = cores[i][cache_set].cache_blocks
                            for j in range(len(core_cache_blocks)):

                                if cores[i][cache_set].cache_blocks[j].tag==cur_tag:
                                    directory_transfers += 1
                                    if cores[i][cache_set].cache_blocks[j].state==State.Modified:
                                        # If a core contains that block in modified state, then put it in owned state
                                        # Also flush out the value (cache to cache transfer)
                                        # Meaning the core containing the block in modified state will give out the value to the requesting core, 
                                        # but will maintain ownership of that block
                                        cores[i][cache_set].cache_blocks[j].state = State.Owned
                                        # print('Cache-to-Cache Flush')

                                    # elif cores[i][cache_set].cache_blocks[j].state==State.Owned:
                                    #     # If the core containing the block is already in owned state,
                                    #     # It will just flush out the value to the requesting core.
                                    #     print('Cache-to-Cache Flush')                                    

                else:
                    # If the directory does not have that block, bring it from memory
                    # Make it present in the directory
                    # print('Copy brought in from memory')
                    Directory[cur_tag].present = True

                # --> Update it in the current cache too
                target_block = cores[thread][cache_set].access_order.pop(0)                
                cores[thread][cache_set].cache_blocks[target_block].state = State.Shared
                cores[thread][cache_set].cache_blocks[target_block].tag = cur_tag
                # print('Copy updated in core ', thread, ' moved to shared state')
                # Update the access order of that cache set too            
                cores[thread][cache_set].access_order.append(target_block)

                # --> Update it in the directory to show that it is now present in the new core requesting it
                Directory[cur_tag].processor_vector[thread] = 1                


        elif (tag_present and tag_state==State.Modified) or (tag_present and tag_state==State.Shared and access_type==0) or (tag_present and tag_state==State.Owned and access_type==0):
            # That block will remain in the same state
            if access_type==0:
                # print('Read Hit')
                read_hits += 1
            else:
                if write_method==2:
                    write_backs += 1
                # print('Write Hit') 
                write_hits += 1

        elif (tag_present and tag_state==State.Shared and access_type==1):
            # Invalid all other copies containing that block
            # print('Write Hit')
            if write_method==2:
                write_backs += 1
            write_hits += 1

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
                                # print('Write back')
                                write_backs += 1

                            # Any other core containing a copy of that block is moved to invalid state from modified, shared or owned state
                            cores[i][cache_set].cache_blocks[j].state==State.Invalid
                            invalidations += 1
                            directory_transfers += 1
                            # print('Copy in procesor ', i, ' in cache set ',cache_set, ' and cache block ', j, ' moved to invalid state')
                            # Update the least recently used list for the cache_blocks of that set.
                            cores[i][cache_set].access_order.remove(j)
                            cores[i][cache_set].access_order.append(j)
                            # The processor vector in the directory is updated to reflect the invalidation
                            Directory[cur_tag].processor_vector[i] = 0

            # Move the current block to modified state from shared state

            # --> Update it in the current cache too
            target_block = cores[thread][cache_set].access_order.pop(0)        
            cores[thread][cache_set].cache_blocks[target_block].state = State.Modified
            cores[thread][cache_set].cache_blocks[target_block].tag = cur_tag
            # print('Copy updated in core ', thread, ' moved to modified state')
            # Update the access order of that cache set too            
            cores[thread][cache_set].access_order.append(target_block)

            # --> Update it in the directory to show that it is now present in the new core requesting it
            Directory[cur_tag].processor_vector[thread] = 1
            # print(Directory[cur_tag].processor_vector)


        elif (tag_present and tag_state==State.Owned and access_type==1):

            if write_method==2:
                write_backs += 1

            # Invalid all other copies containing that block
            # print('Write Hit')
            write_hits += 1
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

                            # Any other core containing a copy of that block is moved to invalid state from modified, shared or owned state
                            cores[i][cache_set].cache_blocks[j].state==State.Invalid
                            invalidations += 1
                            directory_transfers += 1
                            # print('Copy in procesor ', i, ' in cache set ',cache_set, ' and cache block ', j, ' moved to invalid state')
                            # Update the least recently used list for the cache_blocks of that set.
                            cores[i][cache_set].access_order.remove(j)
                            cores[i][cache_set].access_order.append(j)

                            # The processor vector in the directory is updated to reflect the invalidation
                            Directory[cur_tag].processor_vector[i] = 0

            # Move the current block to modified state from shared state

            # --> Update it in the current cache too
            target_block = cores[thread][cache_set].access_order.pop(0)            
            cores[thread][cache_set].cache_blocks[target_block].state = State.Modified
            cores[thread][cache_set].cache_blocks[target_block].tag = cur_tag
            # print('Copy updated in core ', thread, ' moved to modified state')
            # Update the access order of that cache set too            
            cores[thread][cache_set].access_order.append(target_block)

            # --> Update it in the directory to show that it is now present in the new core requesting it
            Directory[cur_tag].processor_vector[thread] = 1
            # print(Directory[cur_tag].processor_vector)

    printSummary(read_misses, write_misses, read_hits, write_hits, invalidations, write_backs, directory_transfers)