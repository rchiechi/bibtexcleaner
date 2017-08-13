#!/usr/bin/env python3
import sys,os,tempfile,shutil,argparse,pickle

try:
    import pip
except ImportError:
    print('You don\'t have pip installed. You will need pip to install other dependencies.')
    sys.exit(1)

prog = os.path.basename(sys.argv[0]).replace('.py','')
installed = [package.project_name for package in pip.get_installed_distributions()]
required = ['colorama','bibtexparser','titlecase','requests','python-Levenshtein']
for pkg in required:
    if pkg not in installed:
        print('You need to install %s to use %s.' % (pkg,prog))
        print('e.g., sudo -H pip3 install --upgrade %s' % pkg)
        sys.exit(1)

import Levenshtein
import requests
from titlecase import titlecase
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.customization import page_double_hyphen
from bibtexparser.latexenc import string_to_latex
from colorama import init,Fore,Back,Style

# Setup colors
init(autoreset=True)

# Parse args
desc = 'Cleanup a bibtex file before submission.'

parser = argparse.ArgumentParser(description=desc,formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('infile', type=str, nargs=1, default=[], 
    help='Bibtex file to parse.')
parser.add_argument('-r','--refresh', action='store_true', default=False,
    help="Refresh cached journal list.")
parser.add_argument('-d','--database', type=str, 
    default = 'https://raw.githubusercontent.com/rchiechi/BibTexCleaner/master/journal_abbreviations_general.txt',
    #default='https://raw.githubusercontent.com/JabRef/reference-abbreviations/master/journals/journal_abbreviations_general.txt',
    help="Databse of journal abbreviations.")
parser.add_argument('-c','--custom', action='append', default=[],
        help="Cust abbreviations separated by equal signs, e.g., -c 'Journal of Kittens=J. Kitt.'\
        You can call this argument more than once. These will be cached.")


opts=parser.parse_args()
#CACHEDIR = os.path.join(os.path.expanduser('~'),os.argv[0]+".cache")
CACHEDIR = tempfile.gettempdir()

if not opts.infile:
    print('%sI need a bib file to parse!' % Fore.RED)
    sys.exit()
elif not os.path.exists(opts.infile[0]):
    print('%s%s does not exist!' % (Fore.RED,opts.infile[0]))

BIBFILE=os.path.abspath(opts.infile[0])
# Make a backup copy
print('%sBacking %s up to %s' % (Fore.YELLOW,os.path.basename(BIBFILE),os.path.basename(BIBFILE)+'.bak'))
shutil.copy2(BIBFILE,BIBFILE+'.bak')

# Use a cache file so we do not have to fetch the abbreviations on each run
JCACHE=os.path.join(CACHEDIR,'journal_abbreviations.cache')

# Remove stale cache if refresh is requested
if os.path.exists(JCACHE) and opts.refresh:
    os.remove(JCACHE)

def getCache():
    '''
    Return a dictionary of journals either from cache or online 
    '''
    journals = {}
    if not os.path.exists(JCACHE):
        print('%sFetching list of common journal abbreviations.' % Fore.YELLOW)
        try:
            r = requests.get(opts.database)
            for l in r.text.split('\n'):
                try:
                    t,a = l.split('=')
                except ValueError:
                    continue
                journals[t.strip()] = a.strip()
                # Some journals/books have parentheticals e.g., (New York, New York)
                # Save the abbreviation both with and without it 
                if '(' in t and '(' in a:
                    journals[t.split('(')[0].strip()] = a.split('(')[0].strip()
        except Exception as msg:
            print("%sError fetching journal abbreviations: %s" % (Fore.RED,str(msg)) )
    else:
        try:
            journals = pickle.load(open(JCACHE,'rb'))
            print('%sRead journal abbreciations from %s.' % (Fore.YELLOW,JCACHE))
        except:
            print('%sError loading cache from %s.' % (Fore.RED,JCACHE))
            sys.exit(1)
    return journals

def putCache(journals):
    try:
        pickle.dump(journals,open(JCACHE,'wb'))
        print('%sSaved cache to %s' % (Fore.YELLOW,JCACHE))
    except:
        print('%sError saving cache to %s' % (Fore.RED,JCACHE))


class RecordHandler():
    def __init__(self,journals):
        self.journals = journals
        self.recordkeys = ('ENTRYTYPE','ID','title','journal','pages','volume')
        self.clean = []
        self.dedupe = []
        self.errors = []
        self.dupes = {}
        self.n_abbreviated = 0
        self.n_cleaned = 0
        self.n_parsed = 0

    def handle_record(self,record):
        self.clean.append(record)
        for key in self.recordkeys:
            if key not in record: # and record['ENTRYTYPE'] == 'journal':
                self.errors.append(record)
                print('%sCannot parse %s' % (Fore.RED,record['ENTRYTYPE']))
                return record
        __abbrev = False
        cleaned = titlecase(record['title'])
        if cleaned != record['title']:
            self.n_cleaned += 1
            self.clean[-1]['title'] = cleaned
        fuzzy,score = self.__fuzzymatch(record['journal'])
        if score >= 0.95:
            __abbrev = True
        else:
            try:
                _j = input('(%0.1f%%) Replace "%s%s%s" with "%s%s%s" or something else? ' % (score*100,Style.BRIGHT+Fore.YELLOW,
                    record['journal'],Style.RESET_ALL,Style.BRIGHT+Fore.GREEN,fuzzy,Style.RESET_ALL))
                if _j.lower() in ('y','yes'):
                    __abbrev = True
                elif _j.lower() in ('n','no',''):
                    pass
                else:
                    fuzzy = _j
                    __abbrev = True
            except KeyboardInterrupt:
                print('')
                sys.exit()
        if __abbrev:
            print('%s%s%s%s -> %s%s%s' % (Style.BRIGHT,Fore.CYAN,record['journal'],
                Fore.WHITE,Fore.CYAN,fuzzy,Style.RESET_ALL))
            self.n_abbreviated += 1
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
        self.n_parsed += 1
        return record

    def __fuzzymatch(self,s):
        n = ('',0)
        for key in self.journals:
            _a = Levenshtein.ratio(s,key)
            _b = Levenshtein.ratio(s,self.journals[key])
            if _a > n[1]: n = [self.journals[key],_a]
            if _b > n[1]: n = [self.journals[key],_b]
        return n

    def dodupecheck(self):
        while self.dedupe:
            _e = self.dedupe.pop()
            for _c in self.dedupe:
                if _e[0:2] == _c[0:2]:
                    if _e[-1] in self.dupes:
                        self.dupes[_e[-1]].append(_c)
                    else:
                        self.dupes[_e[-1]] = [_c]

        if self.dupes:
            print('\nPossible dupes:\n')
            for dupe in self.dupes:
                d = self.dupes[dupe]
                n = 1
                dupelist = { str(n):bib_database.entries_dict[dupe]  }
                for _d in d:
                    n += 1
                    dupelist[str(n)] = bib_database.entries_dict[_d[3]]
                print('\t\t# # #')
                for n in dupelist:
                    print('%s%s%s):   %s%s' % (Style.BRIGHT,Fore.YELLOW,n,Fore.CYAN,dupelist[n]['ID']))
                    print('%sJournal: %s%s%s' %(Fore.YELLOW,Style.BRIGHT,Fore.WHITE,dupelist[n]['journal']))
                    print('%sVolume: %s%s%s' %(Fore.YELLOW,Style.BRIGHT,Fore.WHITE,dupelist[n]['volume']))
                    print('%sPages: %s%s%s' %(Fore.YELLOW,Style.BRIGHT,Fore.WHITE,dupelist[n]['pages']), end='\n\n')
                keep = input('Keep which one?  ')
                if keep not in dupelist:
                    print('%sKeeping all.' % (Fore.GREEN) )
                else:
                    print('%sKeeping %s%s.' % (Style.BRIGHT,Fore.GREEN,dupelist[keep]['ID']))
                    for n in dupelist:
                        if n == keep:
                            continue
                        for i in range(0,len(self.clean)):
                            if self.clean[i]['ID'] == dupelist[n]['ID']:
                                print('%s%sDeleting%s %s%s%s' % (Fore.YELLOW,Back.RED,
                                    Style.RESET_ALL,Style.BRIGHT,Fore.RED,self.clean[i]['ID']))
                                del(self.clean[i])
                                break
    def printstats(self):
        print('%s%sParsed: %s\n%sCleaned: %s\n%sAbbreviated: %s\n%sDupes: %s\n%sFailed:%s%s' % \
                (Style.BRIGHT,Fore.GREEN,self.n_parsed,Fore.YELLOW,
                    self.n_cleaned,Fore.MAGENTA,self.n_abbreviated,
                    Fore.CYAN,len(self.dupes),Fore.RED,len(self.errors),Style.RESET_ALL))
        if len(self.errors):
            print('\nEntries that produced errors:\n')
            #print(self.errors)
            for err in self.errors:
                print('* * * * * * * * * * * * * * * *')
                for key in self.recordkeys:
                    if key not in err:
                        print('%s%s%s: -' % (Fore.RED,titlecase(key),Style.RESET_ALL))
                    else:
                        print('%s: %s%s' % (titlecase(key),Style.BRIGHT,err[key]))

# Parse journal abbreviations
journals = getCache()
# Parse custom abbreviations
journals.update(__parseabbreviations(opts.custom))
# Update cache
putCache(journals)

print("%sRead %s journals." % (Fore.BLUE,len(journals.keys())) )

# Setup BibTex Parser
parser = BibTexParser()
records = RecordHandler(journals)
parser.customization = records.handle_record

print('%s # # # # %s\n' % (Style.BRIGHT,Style.RESET_ALL) )
with open(BIBFILE) as fh:
    bib_database = bibtexparser.load(fh, parser=parser)
print('\n%s # # # # %s' % (Style.BRIGHT,Style.RESET_ALL) )
records.dodupecheck()
# Replace entries in database with cleaned versions
bib_database.entries = records.clean
writer = BibTexWriter()
# Overwrite original BibTex file
with open(BIBFILE, 'w') as bibfile:
        bibfile.write(writer.write(bib_database))
records.printstats()
