#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A script to format a bibtex database as a simple
list of publications in HTML, e.g., for your
group website or CV.
"""
import sys
import os
import argparse
# import cgi
import datetime
import urllib.parse

try:
    from titlecase import titlecase
    import bibtexparser
    from bibtexparser.bparser import BibTexParser
    # from bibtexparser.bwriter import BibTexWriter
    # from bibtexparser.bibdatabase import BibDatabase
    # from bibtexparser.customization import page_double_hyphen
    # from bibtexparser.latexenc import string_to_latex
    import colorama as cm
    import latexcodec #pylint: disable=unused-import

except ImportError as msg:
    print("Error importing package: %s" % str(msg))
    sys.exit(1)

    # Setup colors
cm.init(autoreset=True)


class RecordHandler():

    recordkeys = ('ID','author','title','journal','pages','volume','year')
    doikeys = ('doi', 'eprint', 'note', 'bdsk-url-1', 'uri', 'bdsk-url-2', 'bdsk-url-3')
    def __init__(self,_opts):
        self.opts = _opts
        if self.opts.strong:
            self.bold=('<strong>','</strong>')
        elif self.opts.span:
            self.bold=('<span class="c3">','</span>')
        else:
            self.bold=('<b>','</b>')
        if self.opts.em:
            self.italics=('<em>','</em>')
        elif self.opts.span:
            self.italics=('<span class="c1">','</span>')
        else:
            self.italics=('<i>','</i>')
        if self.opts.span:
            self.normal=('<span class="c2">','</span>')
        else:
            self.normal=('','')
        if self.opts.span:
            self.heading=('<h3>','</h3>')
        else:
            self.heading=self.bold

        self.formatted = {'journals':{},'books':{},'patents':{}}

#<p>Wan, W. Brad; Chiechi, Ryan C; Weakley, T.J.R.; Haley, M.M. <A href="http://doi.org/10.1002/1099-0690(200109)2001:18%3C3485::AID-EJOC3485%3E3.0.CO;2-I" target="_blank">Synthesis and Spectroscopic Studies of Expanded Planar Dehydrotribenzo[n]annulenes Containing One or Two Isolated Alkene Units</A>. <i>Eur. J. Org. Chem.</i> <b>2001</b>, <i>2001</i>, 3485-3490</p></li><li><p>Bell, M.L.; Chiechi, Ryan C; Johnson, C.A.; Kimball, D.B.; Matzger, A.J.; Wan, W. Brad; Weakley, T.J.R.; Haley, M.M. <A href="http://dx.doi.org/10.1016/S0040-4020(01)00229-0" target="_blank">A Versatile Synthetic Route to Dehydrobenzoannulenes via in Situ Generation of Reactive Alkynes</A>. <i>Tetrahedron</i> <b>2001</b>, <i>57</i>, 3507-3520</p>
# <h3>2018</h3>
# <p class="c2"><span>Jia, C.; Famili, M.; Carlotti, M.; Liu, Y.; Wang, P.; Grace, I. M.; Feng, Z.; Wang, Y.; Zhao, Z.; Ding, M.; Xu, X.; Wang, C.; Lee, S.-J.; Huang, Y.; Chiechi, R. C.; Lambert, C. J.; Duan, X. 
# </span><span class="c1">Sci. Adv.</span><span>&nbsp;</span><span class="c3">2018</span><span>, </span><span class="c1">4</span><span class="c0">&nbsp;(10), eaat8237.</span></p><br>
    def outputHTML(self):
        html=[]
        years = list(self.formatted['journals'].keys())
        years.sort(reverse=True)

        html.append('<ol>')
        for _year in years:
            html.append('%s%s%s' % (self.heading[0],_year,self.heading[1]))
            for _pub in self.formatted['journals'][_year]:
                html.append('<li>')
                html.append('<p>%s</p>' % _pub)
                html.append('</li>')
        html.append('</ol>')

        if self.opts.linebreaks:
            return '\n'.join(html)
        else:
            return ''.join(html)

    # def outputFancyHTML(self):
    #     html=[]
    #     years = list(self.formatted['journals'].keys())
    #     years.sort(reverse=True)

    #     html.append('<ol>')
    #     for _year in years:
    #         html.append('<h3>%s</h3>' % _year)
    #         for _pub in self.formatted['journals'][_year]:
    #             html.append('<li>')
    #             html.append('<p>%s</p>' % _pub)
    #             html.append('</li>')
    #     html.append('</ol>')

    #     if self.opts.linebreaks:
    #         return '\n'.join(html)
    #     else:
    #         return ''.join(html)

    def handle_record(self,record):
        _formatted = str()
        for key in self.recordkeys:
            if key not in record:
                if 'ENTRYTYPE' in record:
                    if record['ENTRYTYPE'] in ('article','journal'):
                        print('%sJournal entry missing %s' % (cm.Fore.RED,key))
                        record[key]=''

                    else:
                        self.__parseNonjournal(record)
                        return False
                else:
                    print('%sCannot parse unknown entry.' % cm.Fore.RED)
                    print(record)
                    return False

        try:
            year = int(record['year'])
        except ValueError:
            year = datetime.datetime.now().year
            print("Warning %s is non-numerical year, setting to %s." % (record['year'],year))
        clean_title = titlecase(self.__cleanLatex(record['title']))
        clean_doi = str()


        for key in self.doikeys:
            if key in record:
                if 'doi.org' in record[key].lower():
                    clean_doi = self.__parseDoi(record[key])
                    break
                if 'doi' in record[key].lower():
                    clean_doi = self.__parseDoi(record[key])
                    break

        if clean_doi:
            clean_title = '<A href="%s" target="_blank">%s</A>' % (clean_doi,clean_title)

        #str(bytes(_author.strip(), encoding='latex'),encoding='latin-1')
        clean_authors = self.__parseAuthors(record['author'])
        clean_journal = '%s%s%s' % (self.italics[0],self.__cleanLatex(record['journal']),self.italics[1])
        clean_pages = self.__cleanLatex(record['pages'])
        clean_volume = '%s%s%s' % (self.italics[0],self.__cleanLatex(record['volume']),self.italics[1])
        clean_year = '%s%s%s' % (self.bold[0],self.__cleanLatex(year),self.bold[1])

        _formatted = '%s %s. %s %s, %s, %s' % (clean_authors,
                                clean_title, clean_journal,
                                clean_year, clean_volume, clean_pages)

        if year not in self.formatted['journals']:
            self.formatted['journals'][year]=[_formatted]
        else:
            self.formatted['journals'][year].append(_formatted)

    def __cleanLatex(self,latex):
        _raw = r'{}'.format(latex)
        for _r in ( ('{',''),('}',''),('--','-')):
            _raw = _raw.replace(_r[0],_r[1])
        cleaned= bytes(_raw, encoding='utf8').decode('latex')

        return str(cleaned).strip()

    def __parseAuthors(self,authors):
        _authorlist = []
        for _author in (authors.split('and')):
            _s = self.__cleanLatex(_author)
            if ',' not in _s:
                _s = '%s, %s' % (_s.split(' ')[-1], ' '.join(_s.split(' ')[:-1]))
            if opts.boldname and (opts.boldname in _s):
                _s = '%s%s%s' % (self.bold[0],_s,self.bold[1])
            _authorlist.append(_s)
        return "%s%s%s" % (self.normal[0], '; '.join(_authorlist), self.normal[1])

    def __parseDoi(self,doilink):
        _doi = urllib.parse.urlsplit(doilink.strip())
        if not _doi.netloc:
            _url = "dx.doi.org"
        else:
            _url = _doi.netloc
        return urllib.parse.urlunsplit(['http',
                                        _url,
                                        _doi.path,
                                        '',''])
        #if doi[:4].lower() != 'http':
        #    return 'http://'+doi
        #else:
        #    return doi

    def __parseNonjournal(self,record):
        # TODO: actually parse non-journals
        print('%sPretending to parse non-journal%s' % (cm.Style.BRIGHT,cm.Style.RESET_ALL))
        if not self.formatted['books']:
            self.formatted['books']={'2018':[record]}
        else:
            self.formatted['books']['2018'].append(record)

# Parse args
desc = 'Convert a BibTeX database to HTML.'

parser = argparse.ArgumentParser(
    description=desc,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('infile', type=str, nargs=1, default=[],
    help='Bibtex file to parse.')
parser.add_argument('-b', '--boldname', type=str, default='',
    help='Authors containing this string will be bolded.')
parser.add_argument('--strong', action="store_true", default=False,
    help='Use <strong> instead of <b>')
parser.add_argument('--em', action="store_true", default=False,
    help='Use <em> instead of <i>')
parser.add_argument('--span', action="store_true", default=False,
    help='Use <span> instead of <i>, <br>, etc.')
parser.add_argument('--linebreaks', action="store_true", default=False,
    help='Use linebreaks in HTML output.')
parser.add_argument('-o', '--out', type=str, default='',
    help='Write output to html file instead of stdout.')

opts=parser.parse_args()
if not opts.infile:
    print('%sI need a bib file to parse!' % cm.Fore.RED)
    sys.exit()
elif not os.path.exists(opts.infile[0]):
    print('%s%s does not exist!' % (cm.Fore.RED,opts.infile[0]))


BIBFILE=os.path.abspath(opts.infile[0])
parser = BibTexParser(common_strings=True)
records = RecordHandler(opts)
parser.customization = records.handle_record
print('%s # # # # %s\n' % (cm.Style.BRIGHT,cm.Style.RESET_ALL) )
with open(BIBFILE) as fh:
    try:
        bib_database = bibtexparser.load(fh, parser=parser)
    except KeyError as msg:
        print("Error opening bib file: KeyErorr, %s" % str(msg))
        sys.exit(1)
print('\n%s # # # # %s' % (cm.Style.BRIGHT,cm.Style.RESET_ALL) )

if opts.out:
    with open(opts.out, 'w') as fh:
        fh.write(records.outputHTML())
else:
    print('* * * * * * * * * * * * * * * * * * * * * * * * * * *\n')
    print(records.outputHTML())
