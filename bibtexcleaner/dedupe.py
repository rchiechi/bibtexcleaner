'''Deduping functions'''

import sys

try:
    from colorama import init,Fore,Style,Back

except ImportError as msg:
    print("Error importing package: %s" % str(msg))
    sys.exit(1)

# Setup colors
init(autoreset=True)

def dodupecheck(bib_database):
    '''Check for duplicate bibtex entries'''
    dedupe = []
    dupes = {}
    for record in bib_database.entries:
        try:
            _p = record['pages'].split('-')[0].strip().strip('-')
            _j, _v, _id = record['journal'], record['volume'], record['ID']
            if _p and _v:
                dedupe.append( (_p, _v, _j, _id) )
        except KeyError:
            continue
    while dedupe:
        # Pop a dedupe tuple off the list
        _e = dedupe.pop()
        for _c in dedupe:
            # See if it overlaps with tuples in the list
            if _e[0:2] == _c[0:2]:
                # Create a dictionary of lsts of potential dupes keyed by ID
                if _e[-1] in dupes:
                    dupes[_e[-1]].append(_c)
                else:
                    dupes[_e[-1]] = [_c]
    if dupes:
        return dodedupe(bib_database, dupes)
    return bib_database.entries

def dodedupe(bib_database, dupes):
    '''Function that does the actual deduping'''
    print('\nPossible dupes:\n')
    clean = bib_database.entries
    for _id in dupes:
        # dupe is a tuple (pages, volume, journal, ID)
        dupe = dupes[_id]
        i = 1
        dupelist = { str(i):bib_database.entries_dict[_id]  }
        for _d in dupe:
            i += 1
            dupelist[str(i)] = bib_database.entries_dict[_d[3]]
        print('\t\t# # #')
        for _n in dupelist:
            try:
                print('%s%s%s):   %s%s' % (Style.BRIGHT,Fore.YELLOW,_n,Fore.CYAN,dupelist[_n]['ID'])) #pylint: disable=C0301
                print('%sJournal: %s%s%s' %(Fore.YELLOW,Style.BRIGHT,Fore.WHITE,dupelist[_n]['journal'])) #pylint: disable=C0301
                print('%sVolume: %s%s%s' %(Fore.YELLOW,Style.BRIGHT,Fore.WHITE,dupelist[_n]['volume'])) #pylint: disable=C0301
                print('%sPages: %s%s%s' %(Fore.YELLOW,Style.BRIGHT,Fore.WHITE,dupelist[_n]['pages']), end='\n\n') #pylint: disable=C0301
            except KeyError as msg:
                print("Error parsing entry: %s" % str(msg))
        keep = input('Keep which one?  ')
        if keep not in dupelist:
            print('%sKeeping all.' % (Fore.GREEN) )
        else:
            print('%sKeeping %s%s.' % (Style.BRIGHT,Fore.GREEN,dupelist[keep]['ID']))
            for _n in dupelist:
                if _n == keep:
                    continue
                for _c in enumerate(clean):
                    i = _c[0]
                    if clean[i]['ID'] == dupelist[_n]['ID']:
                        print('%s%sDeleting%s %s%s%s' % (Fore.YELLOW,Back.RED,
                            Style.RESET_ALL,Style.BRIGHT,Fore.RED,clean[i]['ID']))
                        del clean[i]
                        break
    return clean
