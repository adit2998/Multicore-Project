def printSummary(read_misses, write_misses, read_hits, write_hits, invalidations, write_backs, directory_transfers):
    print('Read Misses:         ', read_misses)
    print('Write Misses:        ', write_misses)
    print('Read Hits:           ', read_hits)
    print('Write Hits:          ', write_hits)
    print('Invalidations:       ', invalidations)
    print('Write backs:         ', write_backs)
    print('Directory transfers: ', directory_transfers)