#!/usr/bin/env python3
'''Crawl through a bibtex database and try to find official abbreviations for journals.'''

import sys
import os
import shutil
import argparse
import btcleaner

try:
    import bibtexparser
    from bibtexparser.bparser import BibTexParser
    from bibtexparser.bwriter import BibTexWriter
    from colorama import init,Fore,Style

except ImportError as msg:
    print("Error importing package: %s" % str(msg))
    sys.exit(1)

# Setup colors
init(autoreset=True)

# Parse args
DESC = 'Cleanup a bibtex file before submission.'

parser = argparse.ArgumentParser(description=DESC,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('infile', type=str, nargs=1, default=[],
    help='Bibtex file to parse.')
parser.add_argument('-r','--refresh', action='store_true', default=False,
    help="Refresh cached journal list.")
parser.add_argument('-d','--database', type=str,
    #default = 'https://raw.githubusercontent.com/rchiechi/btcleaner/master/journal_abbreviations_general.txt', #pylint: disable=C0301
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

#TODO this should be more like a merge function
if opts.refresh:
    btcleaner.refresh()
# Parse journal abbreviations from cache or remote
journals = btcleaner.load(opts.database, opts.custom)
# Save the cache to dist (with custom abbreviations)
btcleaner.save(journals)

print("%sRead %s journals." % (Fore.BLUE,len(journals.keys())) )

print('%s # # # # %s\n' % (Style.BRIGHT,Style.RESET_ALL) )
records = btcleaner.getrecordhandler(journals)
bibparser = BibTexParser(common_strings=True,
                         customization=records.handle_record )
with open(BIBFILE) as fh:
    bib_database = bibtexparser.load(fh, parser=bibparser)

print('\n%s # # # # %s' % (Style.BRIGHT,Style.RESET_ALL) )

# Dedupe entries in cleaned database
bib_database.entries = btcleaner.dedupe_database(bib_database)
unique = records.getcustom()
if unique:
    btcleaner.save(btcleaner.load(opts.database, unique))

records.printstats()

try:
    while True:
        _l = input('%sSave changes to %s%s%s? %s(y/n): ' % (
            Style.BRIGHT+Fore.WHITE,
            Fore.YELLOW, BIBFILE, Fore.WHITE,
            Style.RESET_ALL))
        if _l.lower() in ('y', 'yes'):
            break
        if _l.lower() in ('n', 'no'):
            print('%sNot saving changes.%s' % (
                Style.BRIGHT+Fore.MAGENTA,Style.RESET_ALL))
            sys.exit()
except KeyboardInterrupt:
    sys.exit()

writer = BibTexWriter()
# Overwrite original BibTex file
with open(BIBFILE, 'w') as bibfile:
    print('%sSaving changes to %s' % (
        Style.BRIGHT+Fore.GREEN,BIBFILE))
    bibfile.write(writer.write(bib_database))
