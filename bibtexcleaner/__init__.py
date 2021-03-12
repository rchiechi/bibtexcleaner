'''Classes and functions for handling caching and parsing of bibtexentries'''

__all__ = ['refresh', 'load', 'save']

from . import cache, recordhandler

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
