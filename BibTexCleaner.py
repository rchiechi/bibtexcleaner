#!/usr/bin/env python3
'''Crawl through a bibtex database and try to find official abbreviations for journals.'''

import sys
import os
import shutil
import argparse
import bibtexcleaner
from bibtexcleaner.recordhandler import RecordHandler
#The pip version of bibtexparser has a showstopping bug in it
#so I copied it to BibTexCleaner for now
from bibtexcleaner import bibtexparser
from bibtexcleaner.bibtexparser.bparser import BibTexParser
from bibtexcleaner.bibtexparser.bwriter import BibTexWriter

try:
    # import bibtexparser
    # from bibtexparser.bparser import BibTexParser
    # from bibtexparser.bwriter import BibTexWriter
    from colorama import init,Fore,Style

except ImportError as msg:
    print("Error importing package: %s" % str(msg))
    sys.exit(1)



# Setup colors
init(autoreset=True)
# prog = os.path.basename(sys.argv[0]).replace('.py','')

# Parse args
DESC = 'Cleanup a bibtex file before submission.'

parser = argparse.ArgumentParser(description=DESC,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('infile', type=str, nargs=1, default=[],
    help='Bibtex file to parse.')
parser.add_argument('-r','--refresh', action='store_true', default=False,
    help="Refresh cached journal list.")
parser.add_argument('-d','--database', type=str,
    #default = 'https://raw.githubusercontent.com/rchiechi/BibTexCleaner/master/journal_abbreviations_general.txt', #pylint: disable=C0301
    default='https://raw.githubusercontent.com/JabRef/'\
        +'abbrv.jabref.org/master/journals/journal_abbreviations_acs.csv',
    help="Databse of journal abbreviations.")
parser.add_argument('-c','--custom', action='append', default=[],
        help="Cust abbreviations separated by equal signs, e.g., -c 'Journal of Kittens;J. Kitt.'\
        You can call this argument more than once. These will be cached.")


opts=parser.parse_args()

if not opts.infile:
    print('%sI need a bib file to parse!' % Fore.RED)
    sys.exit()
elif not os.path.exists(opts.infile[0]):
    print('%s%s does not exist!' % (Fore.RED,opts.infile[0]))

BIBFILE=os.path.abspath(opts.infile[0])
# Make a backup copy
print('%sBacking %s up to %s' %\
    (Fore.YELLOW,os.path.basename(BIBFILE),os.path.basename(BIBFILE)+'.bak'))
shutil.copy2(BIBFILE,BIBFILE+'.bak')

# Use a cache file so we do not have to fetch the abbreviations on each run
# JCACHE=os.path.join(CACHEDIR,'journal_abbreviations.cache')

if opts.refresh:
    bibtexcleaner.refresh()



# Parse journal abbreviations
journals = bibtexcleaner.load(opts.database, opts.custom)
# Update cache
bibtexcleaner.save(journals)

print("%sRead %s journals." % (Fore.BLUE,len(journals.keys())) )



print('%s # # # # %s\n' % (Style.BRIGHT,Style.RESET_ALL) )
bibparser = BibTexParser()
records = RecordHandler(journals)
bibparser.customization = records.handle_record
with open(BIBFILE) as fh:
    bib_database = bibtexparser.load(fh, parser=bibparser)
    records.add(bib_database)

print('\n%s # # # # %s' % (Style.BRIGHT,Style.RESET_ALL) )
records.dodupecheck()
# Replace entries in database with cleaned versions
bib_database.entries = records.clean
writer = BibTexWriter()
# Overwrite original BibTex file
with open(BIBFILE, 'w') as bibfile:
    bibfile.write(writer.write(bib_database))
records.printstats()
