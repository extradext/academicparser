import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from bs4 import BeautifulSoup


REQUEST_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'


class PaperType(Enum):
    PAPER_TYPE_PMC = 'PMC'
    PAPER_TYPE_ETC = 'ETC'


@dataclass
class CitationString:
    raw_string: str
    authors: Optional[List[str]] = None
    title: Optional[str] = None
    year: Optional[str] = None
    journal: Optional[str] = None
    publisher: Optional[str] = None
    book_title: Optional[str] = None
    volume: Optional[str] = None
    note: Optional[str] = None
    pubmed_path: Optional[str] = None
    pmc_free_article: Optional[str] = None

    def parse(self):
        req_data = 'citation={}'.format(self.raw_string).encode('utf-8')
        req = urllib.request.Request('http://freecite.library.brown.edu/citations/create',
                                     data=req_data, headers={'Accept': 'text/xml'}, method='POST')
        with urllib.request.urlopen(req) as f:
            body = f.read().decode('utf-8')
            soup = BeautifulSoup(body, 'xml')
            self.authors = [e.string.strip() for e in soup.find_all('author')]

            get_string = lambda x: x.string.strip() if x is not None else None
            self.title = get_string(soup.find('title'))
            self.year = get_string(soup.find('year'))
            self.journal = get_string(soup.find('journal'))
            self.publisher = get_string(soup.find('publisher'))
            self.book_title = get_string(soup.find('booktitle'))
            self.volume = get_string(soup.find('volume'))
            self.note = get_string(soup.find('note'))

@dataclass
class Paper:
    type: PaperType
    title: str = ''
    authors: List[str] = field(default_factory=list)
    abstract: str = ''
    references: List[CitationString] = field(default_factory=list)
    pmid: Optional[int] = None
    pmcid: Optional[str] = None
