#!/usr/local/bin/python3
import sys,os,tempfile,shutil,argparse,pickle

try:
    import pip
except ImportError:
    print('You don\'t have pip installed. You will need pip to istall other dependencies.')
    sys.exit(1)

prog = os.path.basename(sys.argv[0]).replace('.py','')
# Need to make this check because ase does not check for dependencies like matplotlib at import
installed = [package.project_name for package in pip.get_installed_distributions()]
required = ['colorama','bibtexparser','titlecase','requests']
for pkg in required:
    if pkg not in installed:
        print('You need to install %s to use %s.' % (pkg,prog))
        print('e.g., sudo -H pip3 install --upgrade %s' % pkg)
        sys.exit(1)

import requests
from titlecase import titlecase
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.customization import homogeneize_latex_encoding,convert_to_unicode
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
    default='https://raw.githubusercontent.com/JabRef/reference-abbreviations/master/journals/journal_abbreviations_general.txt',
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

if os.path.exists(JCACHE) and opts.refresh:
    os.remove(JCACHE)

def getCache():
    journals = {}
    if not os.path.exists(JCACHE):
        print('%sFetching list of common journal abbreviations.' % Fore.YELLOW)
        try:
            r = requests.get('https://raw.githubusercontent.com/JabRef/reference-abbreviations/master/journals/journal_abbreviations_general.txt')
            journals = __parseabbreviations(r.text.split('\n'))
            #journals = __parseabbreviations(str(r.content,encoding='utf-8'))
        except Exception as msg:
            print("%sError fetching journal abbreviations: %s" % (Fore.RED,str(msg)) )
    else:
        try:
            journals = pickle.load(open(JCACHE,'rb'))
            print('%sRead journal abbreciations from %s.' % (Fore.YELLOW,JCACHE))
        except:
            print('%sError loading cache from %s.' % (Fore.RED,JCACHE))
            sys.exit()
    return journals

def putCache(journals):
    try:
        pickle.dump(journals,open(JCACHE,'wb'))
        print('%sSaved cache to %s' % (Fore.YELLOW,JCACHE))
    except:
        print('%sError saving cache to %s' % (Fore.RED,JCACHE))

def __parseabbreviations(jlines):
    journals = {}
    for l in jlines:
        try:
            t,a = l.split('=')
        except ValueError as msg:
            continue
        journals[t.strip()] = a.strip()
        if len(t.split('(')) > 1:
            journals[t.split('(')[0].strip()] = a.split('(')[0].strip()
    return journals

# Parse journal abbreviations
journals = getCache()
# Parse custom abbreviations
journals.update(__parseabbreviations(opts.custom))
# Update cache
putCache(journals)


print("%sRead %s journals." % (Fore.BLUE,len(journals.keys())) )

# Setup BibTex Parser
parser = BibTexParser()
parser.customization = convert_to_unicode
with open(BIBFILE) as fh:
    bib_database = bibtexparser.load(fh, parser=parser)

print('%s # # # # %s\n' % (Style.BRIGHT,Style.RESET_ALL) )

# Counters
n = 0
f = []
c= 0
# List for clean entries
clean = []
dedupe = []
# Loop over entries in bibtex database
for bib in bib_database.entries:
    n += 1
    try:
        cleaned = titlecase(bib['title'])
        clean.append(bib)
        if cleaned != bib['title']:
            c += 1
            clean[-1]['title'] = cleaned
        if bib['journal'] in journals and bib['journal'] != journals[bib['journal']]:
            print('%s%s%s%s -> %s%s%s' % (Style.BRIGHT,Fore.CYAN,bib['journal'],
                Fore.WHITE,Fore.CYAN,journals[bib['journal']],Style.RESET_ALL))
            clean[-1]['journal'] = journals[bib['journal']]
        try:
            _p = clean[-1]['pages'].split('-')[0]
        except ValueError:
            _p = clean[-1]['pages']
        _j, _v, _c = clean[-1]['journal'],clean[-1]['volume'],clean[-1]['ID']
        dedupe.append( (_p, _v, _j, _c) )
    except KeyError:
        if bib['ENTRYTYPE'] == 'journal':
            f.append(bib)
print('\n%s # # # # %s' % (Style.BRIGHT,Style.RESET_ALL) )

dupes = []
# De-dupe check
while dedupe:
    _e = dedupe.pop()
    for _c in dedupe:
        if _e[0:2] == _c[0:2]:
            dupes.append( (_e,_c) )
    

# Replace entries in database with cleaned versions
bib_database.entries = clean
writer = BibTexWriter()
# Overwrite original BibTex file
with open(BIBFILE, 'w') as bibfile:
        bibfile.write(writer.write(bib_database))
print('%s%sParsed: %s\n%sCleaned: %s\n%sDupes: %s\n%sFailed:%s%s' % \
        (Style.BRIGHT,Fore.GREEN,n,Fore.YELLOW,c,Fore.CYAN,len(dupes),Fore.RED,len(f),Style.RESET_ALL))
if len(f):
    print('\nEntries that produced errors:\n')
    print(f)

if len(dupes):
    print('\nPossible dupes:\n')
    for d in dupes:
        print('\t\t# # #')
        a = bib_database.entries_dict[d[0][3]]
        b = bib_database.entries_dict[d[1][3]]
        print('   %s%s%s\t%s' % (Style.BRIGHT,Fore.CYAN,a['ID'],b['ID']))
        print('%sJournal: %s%s%s\t%s' %(Fore.YELLOW,Style.BRIGHT,Fore.WHITE,a['journal'],b['journal']))
        print('%sVolume: %s%s%s\t\t%s' %(Fore.YELLOW,Style.BRIGHT,Fore.WHITE,a['volume'],b['volume']))
        print('%sPages: %s%s%s\t%s' %(Fore.YELLOW,Style.BRIGHT,Fore.WHITE,a['pages'],b['pages']))
