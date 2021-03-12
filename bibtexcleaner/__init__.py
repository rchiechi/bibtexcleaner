'''Classes and functions for handling caching and parsing of bibtexentries'''

__all__ = ['refresh', 'load', 'save', 'dedupe_database']

from . import cache, dedupe

def refresh():
    '''Call refershcache function from cache'''
    cache.refreshcache()

def load(database, _custom=None):
    '''Call getcache function from cache and refresh if there is an error.'''
    _journals = cache.getcache(database, _custom=None)
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
