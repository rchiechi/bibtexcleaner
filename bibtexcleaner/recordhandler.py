'''The main class for parsing BiBTeX records'''
import sys

try:
    import Levenshtein #pip3 install python-levenshtein
    from titlecase import titlecase
    from bibtexparser.customization import page_double_hyphen
    from bibtexparser.latexenc import string_to_latex
    from colorama import init,Fore,Back,Style

except ImportError as msg:
    print("Error importing package: %s" % str(msg))
    sys.exit(1)

# Setup colors
init(autoreset=True)



def convertmonth(month_str):
    '''Convert months between numbers and abbreviations.'''
    months_abr={'jan':1,
            'feb':2,
            'mar':3,
            'apr':4,
            'may':5,
            'jun':6,
            'jul':7,
            'aug':8,
            'sep':9,
            'oct':10,
            'nov':11,
            'dec':12}
    months={'january':1,
            'february':2,
            'march':3,
            'april':4,
            'may':5,
            'june':6,
            'july':7,
            'august':8,
            'september':9,
            'october':10,
            'november':11,
            'december':12}

    try:
        month_num = months_abr[month_str.lower()]
    except KeyError:
        try:
            month_num = months[month_str.lower()]
        except KeyError:
            month_num = 0
    return str(month_num)


class RecordHandler():
    '''Handle BibTex Records for the cleaner'''

    recordkeys = ('ENTRYTYPE','ID','title','journal','pages','volume')

    def __init__(self, _journals):
        self.journals = _journals
        self.bib_database = None
        self.clean = []
        self.dedupe = []
        self.errors = []
        self.dupes = {}
        self.history = {}
        # self.n_abbreviated = 0
        # self.n_cleaned = 0
        # self.n_parsed = 0
        self.stats = {'n_cleaned':0,
                      'n_parsed':0,
                      'n_abbreviated':0}

    def add(self, bib_database):
        '''Add a bibtexparser database for later deduping'''
        self.bib_database = bib_database

    def handle_record(self,record):
        '''Main record handling method'''
        self.clean.append(record)
        for key in RecordHandler.recordkeys:
            if key not in record: # and record['ENTRYTYPE'] == 'journal':
                self.errors.append(record)
                print('%sCannot parse %s' % (Fore.RED,record['ENTRYTYPE']))
                return record
        __abbrev = False
        cleaned = titlecase(record['title'])
        if cleaned != record['title']:
            self.stats['n_cleaned'] += 1
            self.clean[-1]['title'] = cleaned
        # File entries are pointless in shared bib files
        for key in ('file','bdsk-file-1'):
            if key in self.clean[-1]:
                del self.clean[-1][key]
        # Non-numeric months do not sort
        if 'month' in record:
            if convertmonth(record['month']):
                record['month']=convertmonth(record['month'])
        # Names should be separated by 'and'; comma is to reverse name/surname order
        if 'author' in record:
            # print(record['author'].split(','))
            if ' and ' not in record['author'] and ',' in record['author']:
                authors=[]
                for author in record['author'].split(','):
                    authors.append('{'+author.strip()+'}')
                record['author'] = " and ".join(authors)

        fuzzy,score = self.__fuzzymatch(record['journal'])
        if record['journal'] in self.history:
            fuzzy = self.history[record['journal']]
            __abbrev = bool(fuzzy)
        elif score > 0.95:
            __abbrev = True
        else:
            try:
                _j = input('(%0.1f%%) Replace "%s%s%s" with "%s%s%s" or something else? ' % (
                    score*100,Style.BRIGHT+Fore.YELLOW,
                    record['journal'],Style.RESET_ALL,
                    Style.BRIGHT+Fore.GREEN,
                    fuzzy,Style.RESET_ALL))
                if _j.lower() in ('y','yes'):
                    __abbrev = True
                elif _j.lower() in ('n','no',''):
                    self.history[record['journal']] = None
                elif _j:
                    fuzzy = _j
                    __abbrev = True
            except KeyboardInterrupt:
                print('')
                sys.exit()

        if __abbrev:
            self.history[record['journal']] = fuzzy
            print('%s%s%s%s -> %s%s%s' % (Style.BRIGHT,Fore.CYAN,record['journal'],
                Fore.WHITE,Fore.CYAN,fuzzy,Style.RESET_ALL))
            self.stats['n_abbreviated'] += 1
            self.clean[-1]['journal'] = fuzzy
            record['journal'] = fuzzy
        try:
            _p = self.clean[-1]['pages'].split('-')[0]
        except ValueError:
            _p = self.clean[-1]['pages']
        _j, _v, _c = self.clean[-1]['journal'],self.clean[-1]['volume'],self.clean[-1]['ID']
        self.dedupe.append( (_p, _v, _j, _c) )
        record['journal'] = string_to_latex(record['journal'])
        record = page_double_hyphen(record)
        self.stats['n_parsed'] += 1
        return record

    def __fuzzymatch(self,journal):
        '''Private method to do a fuzzy match of journal names'''
        i = ('',0)
        for key in self.journals:
            _a = Levenshtein.ratio(journal,key) #pylint: disable=E1101
            _b = Levenshtein.ratio(journal,self.journals[key]) #pylint: disable=E1101
            if _a > i[1]:
                i = [self.journals[key],_a]
            if _b > i[1]:
                i = [self.journals[key],_b]
        return i

    def dodupecheck(self):
        '''Check for duplicate bibtex entries'''
        if self.bib_database is None:
            raise AttributeError('Cannot dedupe before a bibdatabase has been added.')
        while self.dedupe:
            _e = self.dedupe.pop()
            for _c in self.dedupe:
                if _e[0:2] == _c[0:2]:
                    if _e[-1] in self.dupes:
                        self.dupes[_e[-1]].append(_c)
                    else:
                        self.dupes[_e[-1]] = [_c]
        if self.dupes:
            self.__dodedupe()

    def __dodedupe(self):
        '''Private method to do the actual deduping'''
        print('\nPossible dupes:\n')
        for dupe in self.dupes:
            _dups = self.dupes[dupe]
            i = 1
            dupelist = { str(i):self.bib_database.entries_dict[dupe]  }
            for _d in _dups:
                i += 1
                dupelist[str(i)] = self.bib_database.entries_dict[_d[3]]
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
                    for i in range(0,len(self.clean)):
                        if self.clean[i]['ID'] == dupelist[_n]['ID']:
                            print('%s%sDeleting%s %s%s%s' % (Fore.YELLOW,Back.RED,
                                Style.RESET_ALL,Style.BRIGHT,Fore.RED,self.clean[i]['ID']))
                            del self.clean[i]
                            break

    def printstats(self):
        '''Print stats in pretty colors'''
        print('%s%sParsed: %s\n%sCleaned: %s\n%sAbbreviated: %s\n%sDupes: %s\n%sFailed:%s%s' % \
                (Style.BRIGHT,Fore.GREEN,self.stats['n_parsed'],Fore.YELLOW,
                    self.stats['n_cleaned'],Fore.MAGENTA,self.stats['n_abbreviated'],
                    Fore.CYAN,len(self.dupes),Fore.RED,len(self.errors),Style.RESET_ALL))
        if self.errors:
            print('\nEntries that produced errors:\n')
            #print(self.errors)
            for err in self.errors:
                print('* * * * * * * * * * * * * * * *')
                for key in RecordHandler.recordkeys:
                    if key not in err:
                        print('%s%s%s: -' % (Fore.RED,titlecase(key),Style.RESET_ALL))
                    else:
                        print('%s: %s%s' % (titlecase(key),Style.BRIGHT,err[key]))
