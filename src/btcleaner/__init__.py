'''Classes and functions for handling caching and parsing of bibtexentries'''

__version__ = "0.1"
__author__ = 'Ryan C. Chiechi'
__credits__ = 'University of Groningen'

__all__ = ['refresh', 'load', 'save', 'dedupe_database']

from . import cache, dedupe, recordhandler

def refresh():
    '''Call refershcache function from cache'''
    cache.refreshcache()

def load(database, _custom=None):
    '''Call getcache function from cache and refresh if there is an error.'''
    _journals = cache.getcache(database, _custom)
    if not _journals:
        refresh()
        _journals = cache.getcache(database, _custom)
    return _journals

def save(_journals):
    '''Call putcache from cache'''
    cache.putcache(_journals)

def dedupe_database(bib_database):
    '''Call the dedupecheck funnction'''
    return dedupe.dodupecheck(bib_database)

def getrecordhandler(journals):
    '''Return a RecordHandler instance'''
    return recordhandler.RecordHandler(journals)
