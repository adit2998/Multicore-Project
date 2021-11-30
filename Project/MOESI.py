import enum
from os import read
from Summary import printSummary

class State(enum.Enum):
    Invalid = 1
    Modified = 2
    Shared = 3
    Exclusive = 4
    Owned = 5

def MOESI_direct_mapping(instructions, cores, Directory, tag_bits, cache_blocks_bits, write_method):
    print('MOESI Protocol with Direct Mapping')

    read_misses, write_misses, read_hits, write_hits, invalidations, write_backs, directory_transfers = 0, 0, 0, 0, 0, 0, 0

    for time, thread, addr, access_type, access_bytes in instructions:
        addr = "{0:032b}".format(int(addr, 16))
        cache_set = addr[tag_bits:tag_bits+cache_blocks_bits]
        cache_set = int(cache_set, 2)

        cur_tag = addr[:tag_bits]
        cur_tag = int(cur_tag, 2)

        time, thread, access_type, access_bytes = int(time), int(thread), int(access_type), int(access_bytes)

        if cores[thread][cache_set].state==State.Invalid or cores[thread][cache_set].tag!=cur_tag:
            # Miss on invalid state
            if access_type==1:
                # print('Write Miss')
                write_misses += 1
                if Directory[cur_tag].present:
                    # Go to every processor that contains a copy of this block and invalidate it.
                    processors = Directory[cur_tag].processor_vector
                    for i in range(len(processors)):
                        if Directory[cur_tag].processor_vector[i]:
                            if cores[i][cache_set].state==State.Modified or cores[i][cache_set].state==State.Owned:
                                # If the block was in modified state
                                # Then do a write back to main memory before putting that block from directory in invalid state. (Flush)                
                                # print('Write back')
                                write_backs +=1 
                            
                            # elif cores[i][cache_set].state==State.Shared or cores[i][cache_set].state==State.Exclusive:
                            #     print('Cache-to-Cache Flush')

                            # The copy is invalidated in the core if it was previously in modified, shared, or exclusive state.
                            cores[i][cache_set].state = State.Invalid
                            invalidations += 1
                            directory_transfers += 1
                            # print('Copy in procesor ', i, ' moved to invalid state')
                            # The processor vector in the directory is updated to reflect the invalidation
                            Directory[cur_tag].processor_vector[i] = 0

                else:
                    # If the directory does not have that block, bring it from memory.
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
                only_copy = True
                # Check if the block is in directory, Else fetch from memory.
                if Directory[cur_tag].present:
                    # Means it has been previously brought in from main memory.
                    processors = Directory[cur_tag].processor_vector
                    for i in range(len(processors)):                    
                        if Directory[cur_tag].processor_vector[i]:
                            directory_transfers += 1
                            # If another core has that block in modified state, then put it in owned state.
                            if cores[i][cache_set].state==State.Modified or cores[i][cache_set].state==State.Owned:                                
                                # If a core contains that block in modified state, then put it in owned state
                                # Also flush out the value (cache to cache transfer)
                                # Meaning the core containing the block in modified state will give out the value to the requesting core, 
                                # but will maintain ownership of that block
                                cores[i][cache_set].state = State.Owned
                                # print('Cache-to-Cache Flush')                                

                            else:
                                # If that copy was previously in exclusive state, then move it to shared state.
                                # If that copy was previously in shared state, then it will stay in shared state.
                                # if cores[i][cache_set].state==State.Exclusive:
                                #     # If the block was in an exclusive state in another processor, then flush out a value
                                #     print('Cache-to-Cache Flush')

                                cores[i][cache_set].state = State.Shared                                
                            
                            # Indicate there are other copies holding that block
                            only_copy = False
                            
                else:
                    # If the directory does not have that block, bring it in from memory
                    # Make it present in the directory.
                    # print('Copy brought in from memory')
                    Directory[cur_tag].present = True

                if not only_copy:
                    # If there are other cores holding a copy of that cache line, then put that block in shared state. 
                    cores[thread][cache_set].state = State.Shared
                else:
                    # If there are no other cores holding a copy of that cache line, then put that block in exclusive state.
                    cores[thread][cache_set].state = State.Exclusive

                cores[thread][cache_set].tag = cur_tag

                # --> Update it in the directory to show that it is now present in the new core requesting it
                Directory[cur_tag].processor_vector[thread] = 1
                # print(Directory[cur_tag].processor_vector)



        elif (cores[thread][cache_set].state==State.Modified and cores[thread][cache_set].tag==cur_tag) or (cores[thread][cache_set].state==State.Owned and cores[thread][cache_set].tag==cur_tag and access_type==0) or (cores[thread][cache_set].state==State.Exclusive and cores[thread][cache_set].tag==cur_tag and access_type==0) or (cores[thread][cache_set].state==State.Shared and cores[thread][cache_set].tag==cur_tag and access_type==0):
            # Do nothing
            # That block will remain in the same state
            if access_type==0:
                # print('Read Hit')
                read_hits += 1
            else:
                if write_method==2:
                    write_backs += 1
                # print('Write Hit')
                write_hits += 1


        elif (cores[thread][cache_set].state==State.Owned and cores[thread][cache_set].tag==cur_tag and access_type==1) or (cores[thread][cache_set].state==State.Shared and cores[thread][cache_set].tag==cur_tag and access_type==1):
            if write_method==2:
                write_backs += 1
            write_hits += 1
            processors = Directory[cur_tag].processor_vector
            for i in range(len(processors)):                    
                if Directory[cur_tag].processor_vector[i]:                    
                    # Invalidate any other copy that is in owned state or shared state
                    # Bus upgrade from owned or shared to invalid state
                    cores[i][cache_set].state = State.Invalid                                                
                    # There wont be any copy in exclusive state. 
                    invalidations += 1
                    directory_transfers += 1
                    # The processor vector in the directory is updated to reflect the invalidation
                    Directory[cur_tag].processor_vector[i] = 0

            # --> Change the state of that block in the current processor to modified. Also update the tag
            cores[thread][cache_set].state = State.Modified
            cores[thread][cache_set].tag = cur_tag
            # print('Copy updated in core ', thread)            

            # --> Update it in the directory to reflect that the block is only now present in that one core requesting it.
            Directory[cur_tag].processor_vector[thread] = 1
            # print(Directory[cur_tag].processor_vector)

        elif (cores[thread][cache_set].state==State.Exclusive and cores[thread][cache_set].tag==cur_tag and access_type==1):
            if write_method==2:
                write_backs += 1
            write_hits += 1
            # --> Change the state of that block in the current processor to modified. Also update the tag
            cores[thread][cache_set].state = State.Modified
            cores[thread][cache_set].tag = cur_tag
            # print('Copy updated in core ', thread)            

            # --> Update it in the directory to reflect that the block is only now present in that one core requesting it.
            Directory[cur_tag].processor_vector[thread] = 1
            # print(Directory[cur_tag].processor_vector)

        else:
            if access_type==0:
                # print('Read Hit')
                read_hits += 1
            else:
                # print('Write Hit')
                write_hits += 1

    printSummary(read_misses, write_misses, read_hits, write_hits, invalidations, write_backs, directory_transfers)

def MOESI_set_associative(instructions, cores, Directory, tag_bits, cache_set_bits, write_method):
    print('MOESI Protocol with Set-Associative mapping')

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
                                    if cores[i][cache_set].cache_blocks[j].state==State.Modified or cores[i][cache_set].cache_blocks[j].state==State.Owned:
                                        # Then do a write back to main memory before putting that block from directory in shared state.                
                                        # print('Write back')
                                        write_backs += 1

                                    # elif cores[i][cache_set].cache_blocks[j].state==State.Shared or cores[i][cache_set].cache_blocks[j].state==State.Exclusive:
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
                # print('Read Miss')
                read_misses += 1
                only_copy = True

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
                                    directory_transfers += 1

                                    if cores[i][cache_set].cache_blocks[j].state==State.Modified or cores[i][cache_set].cache_blocks[j].state==State.Owned:
                                        
                                        cores[i][cache_set].cache_blocks[j].state==State.Owned
                                        # print('Cache-to-Cache Flush')                                        

                                    else:
                                        # if cores[i][cache_set].cache_blocks[j].state==State.Exclusive:
                                        #     print('Cache-to-Cache Flush')

                                        cores[i][cache_set].cache_blocks[j].state==State.Shared
                                        # print('Copy in procesor ', i, ' moved to shared state')

                                    # Indicating that there are other cores holding that copy.
                                    only_copy = False            
                            
                else:
                    # If the directory does not have that block, bring it from memory
                    # Make it present in the directory
                    # print('Copy brought in from memory')
                    Directory[cur_tag].present = True

                # --> Update it in the current cache too
                target_block = cores[thread][cache_set].access_order.pop(0)            
                
                if not only_copy:
                    cores[thread][cache_set].cache_blocks[target_block].state = State.Shared
                    # print('Copy updated in core ', thread, ' moved to shared state')
                else:
                    # Since there are no other processors holding that copy, then move to exclusive state in the current core requesting it.
                    cores[thread][cache_set].cache_blocks[target_block].state = State.Exclusive
                    # print('Copy updated in core ', thread, ' moved to exclusive state')
                
                cores[thread][cache_set].cache_blocks[target_block].tag = cur_tag            
                # Update the access order of that cache set too            
                cores[thread][cache_set].access_order.append(target_block)
                # --> Update it in the directory to show that it is now present in the new core requesting it
                Directory[cur_tag].processor_vector[thread] = 1                
                    
        elif (tag_present and tag_state==State.Modified) or (tag_present and tag_state==State.Shared and access_type==0) or (tag_present and tag_state==State.Owned and access_type==0) or (tag_present and tag_state==State.Exclusive and access_type==0):
            # That block will remain in the same state
            if access_type==0:
                # print('Read Hit')
                read_hits += 1
            else:
                if write_method==2:
                    write_backs += 1
                # print('Write Hit') 
                write_hits += 1

        elif (tag_present and tag_state==State.Owned and access_type==1) or (tag_present and tag_state==State.Shared and access_type==1):
            
            if write_method==2:
                write_backs += 1
            # print('Write Hit') 
            write_hits += 1

            # Invalidate other copies containing that block
            # Go to every other processor that contains this copy and invalidate it
            processors = Directory[cur_tag].processor_vector
            for i in range(len(processors)):
                if Directory[cur_tag].processor_vector[i]:  
                    # If a core has that tag in its cache set,
                    # Then go to every cache block associated with that set and find the tag before invalidating it. 
                    core_cache_blocks = cores[i][cache_set].cache_blocks
                    for j in range(len(core_cache_blocks)):

                        if cores[i][cache_set].cache_blocks[j].tag==cur_tag:                        

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


        elif (tag_present and tag_state==State.Exclusive and access_type==1):
            if write_method==2:
                write_backs += 1
            # print('Write Hit') 
            write_hits += 1

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

        else:
            if access_type==0:
                read_hits+=1
                # print('Read Hit')
            else:
                if write_method==2:
                    write_backs += 1
                # print('Write Hit') 
                write_hits += 1            

    printSummary(read_misses, write_misses, read_hits, write_hits, invalidations, write_backs, directory_transfers)