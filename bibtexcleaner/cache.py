'''Simple caching functions for journal abbreviations'''
import sys
import os
import tempfile
import pickle

try:
    import requests
    from colorama import init,Fore
except ImportError as msg:
    print("Error importing package: %s" % str(msg))
    sys.exit(1)

# Setup colors
init(autoreset=True)

CACHEDIR = tempfile.gettempdir()
JCACHE=os.path.join(CACHEDIR,'journal_abbreviations.cache')


def refreshcache():
    '''Delete the ondisk cache'''
    if os.path.exists(JCACHE):
        os.remove(JCACHE)

def getcache(database, _custom=None):
    '''Fetch journals from disk cache.'''
    # custom = _custom or {}
    journals = {}
    if not os.path.exists(JCACHE):
        print('%sFetching list of common journal abbreviations.' % Fore.YELLOW)
        _r = requests.get(database)
        if _r.status_code != 200:
            print("%sError fetching journal abbreviations with code %s" %\
                (Fore.RED,str(_r.status_code)) )
        else:
            journals = __parseabbreviations(_r.text.split('\n'))
    else:
        try:
            journals = pickle.load(open(JCACHE,'rb'))
            print('%sRead journal abbreciations from %s.' % (Fore.YELLOW,JCACHE))
        except OSError:
            print('%sError loading cache from %s.' % (Fore.RED,JCACHE))
            return {}
    if isinstance(_custom, dict):
        journals.update(__parseabbreviations(_custom))
    return journals

def putcache(journals):
    '''Save cache to disk'''
    try:
        pickle.dump(journals,open(JCACHE,'wb'))
        print('%sSaved cache to %s' % (Fore.YELLOW,JCACHE))
    except OSError:
        print('%sError saving cache to %s' % (Fore.RED,JCACHE))

def __parseabbreviations(jlines):
    '''Parse abbreviations in the format full name;abbreviation'''
    journals = {}
    for _l in jlines:
        _t, _a = None, None
        for _delim in (';', '='):
            try:
                _t,_a = _l.split(_delim)
            except ValueError:
                continue
        if _t is None or _a is None:
            continue
        journals[_t.strip()] = _a.strip()
        if len(_t.split('(')) > 1:
            journals[_t.split('(')[0].strip()] = _a.split('(')[0].strip()
    return journals