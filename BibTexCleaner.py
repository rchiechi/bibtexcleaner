#!/usr/local/bin/python3
import sys,os,tempfile,shutil

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
YELLOW=Fore.YELLOW
WHITE=Fore.WHITE
RED=Fore.RED
TEAL=Fore.CYAN
GREEN=Fore.GREEN
BLUE=Fore.BLUE
RS=Style.RESET_ALL


CACHEDIR = tempfile.gettempdir()

#TODO actually parse the command line
if len(sys.argv) < 2:
    print('%sI need a bib file to parse!' % RED)
    sys.exit()
elif not os.path.exists(sys.argv[1]):
    print('%s%s does not exist!' % (RED,sys.argv[1]))

BIBFILE=os.path.abspath(sys.argv[1])
print('%sBacking %s up to %s' % (YELLOW,os.path.basename(BIBFILE),os.path.basename(BIBFILE)+'.bak'))
shutil.copy(BIBFILE,BIBFILE+'.bak')

JCACHE=os.path.join(CACHEDIR,'journal_abbreviations_general.txt')
jstr = ''

if not os.path.exists(JCACHE):
    print('%sFetching list of common journal abbreviations.' % YELLOW)
    try:
        r = requests.get('https://raw.githubusercontent.com/JabRef/reference-abbreviations/master/journals/journal_abbreviations_general.txt')
        jstr = str(r.content,encoding='utf-8')
        with open(JCACHE,'wb') as fh:
            fh.write(r.content)
    except Exception as msg:
        print("%sError fetching journal abbreviations: %s" % (RED,str(msg)) )
else:
    print('%sReading journal abbreciations from cache.' % YELLOW)
    with open(JCACHE,'rt') as fh:
        jstr = str(fh.read())

# Parse journal abbreviations
journals = {}
for l in jstr.split('\n'):
    try:
        t,a = l.split('=')
    except ValueError as msg:
        continue
    journals[t.strip()] = a.strip()

print("%sRead %s journals." % (BLUE,len(journals.keys())) )



# Setup BibTex Parser
parser = BibTexParser()
parser.customization = convert_to_unicode
with open(BIBFILE) as fh:
    bib_database = bibtexparser.load(fh, parser=parser)

print('%s # # # # %s\n' % (Style.BRIGHT,RS) )

# Counters
n = 0
f = []
c= 0
# List for clean entries
clean = []
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
            print('%s%s%s%s -> %s%s%s' % (Style.BRIGHT,TEAL,bib['journal'],WHITE,TEAL,journals[bib['journal']],RS))
            clean[-1]['journal'] = journals[bib['journal']]
    except KeyError:
        if bib['ENTRYTYPE'] == 'journal':
            f.append(bib)
print('\n%s # # # # %s' % (Style.BRIGHT,RS) )

# Replace entries in database with cleaned versions
bib_database.entries = clean
writer = BibTexWriter()
# Overwrite original BibTex file
with open(BIBFILE, 'w') as bibfile:
        bibfile.write(writer.write(bib_database))
print('%s%sParsed: %s\n%sCleaned: %s\n%sFailed:%s%s' % (Style.BRIGHT,GREEN,n,YELLOW,c,RED,len(f),RS))
if len(f):
    print('\nEntries that produced errors:\n')
    print(f)
