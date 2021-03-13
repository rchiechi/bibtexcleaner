# BibTexCleaner
An interactive script to cleanup bibtex entries using bibtexparser.
Bibtexcleaner will walk through the entries in a BibTex database and try to guess at the appropriate abbreviations for journal names. It will also try to clean up lists of authors and make titles uniform.

Usage:

bibtexcleaner references.bib

bibtexcleaner references.bib -c 'Journal of Kittens;J. Kitt.' 'Journal of Puppies;J. Pup.'

BibTexCleaner -d 'https://raw.githubusercontent.com/JabRef/abbrv.jabref.org/master/journals/journal_abbreviations_acs.csv'
