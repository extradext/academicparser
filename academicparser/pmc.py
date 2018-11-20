import urllib.request
from html.parser import HTMLParser
from typing import Optional

from bs4 import BeautifulSoup

from academicparser.model import Paper, PaperType, ReferenceString

REQUEST_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
PMC_PAPER_URL_FORMAT = 'https://www.ncbi.nlm.nih.gov/pmc/articles/{}/'

class PMCHtmlParser(HTMLParser):
    PARSER_STATE_IDLE = 0
    PARSER_STATE_TITLE = 1
    PARSER_STATE_AUTHOR_LIST = 2
    PARSER_STATE_AUTHOR_ELEMENT = 3
    PARSER_STATE_ABSTRACT = 4

    def __init__(self, paper):
        super().__init__()
        self.paper = paper

        self.parser_state = PMCHtmlParser.PARSER_STATE_IDLE

    def handle_starttag(self, tag, attrs):
        attr_dict = {e[0]: e[1] for e in attrs}

        if self.parser_state == PMCHtmlParser.PARSER_STATE_IDLE:
            if tag == 'h1':
                if 'class' in attr_dict and attr_dict['class'] == 'content-title':
                    self.parser_state = PMCHtmlParser.PARSER_STATE_TITLE
            elif tag == 'div':
                if 'class' in attr_dict and attr_dict['class'] == 'contrib-group fm-author':
                    self.parser_state = PMCHtmlParser.PARSER_STATE_AUTHOR_LIST
        elif self.parser_state == PMCHtmlParser.PARSER_STATE_AUTHOR_LIST:
            if tag == 'a':
                self.parser_state = PMCHtmlParser.PARSER_STATE_AUTHOR_ELEMENT

    def handle_data(self, data):
        if self.parser_state == PMCHtmlParser.PARSER_STATE_TITLE:
            self.paper.title = data
        elif self.parser_state == PMCHtmlParser.PARSER_STATE_AUTHOR_ELEMENT:
            self.paper.authors.append(data)

    def handle_endtag(self, tag):
        if self.parser_state == PMCHtmlParser.PARSER_STATE_TITLE:
            if tag == 'h1':
                self.parser_state = PMCHtmlParser.PARSER_STATE_IDLE
        elif self.parser_state == PMCHtmlParser.PARSER_STATE_AUTHOR_LIST:
            if tag == 'div':
                self.parser_state = PMCHtmlParser.PARSER_STATE_IDLE
        elif self.parser_state == PMCHtmlParser.PARSER_STATE_AUTHOR_ELEMENT:
            if tag == 'a':
                self.parser_state = PMCHtmlParser.PARSER_STATE_AUTHOR_LIST


def parse(pmcid: str) -> Optional[Paper]:
    paper = Paper(PaperType.PAPER_TYPE_ETC)
    paper.pmcid = pmcid

    paper_url: str = PMC_PAPER_URL_FORMAT.format(pmcid)

    req = urllib.request.Request(paper_url)
    req.add_header('User-Agent', REQUEST_USER_AGENT)
    with urllib.request.urlopen(req) as f:
        if f.status == 200:
            content_type = f.info()['Content-Type']
            charset = content_type.split(';')[-1].split('=')[-1]

            res_body = f.read().decode(charset)

            soup = BeautifulSoup(res_body, 'html.parser')
            paper.title = soup.find('h1', class_='content-title').string

            authors_container = soup.find('div', class_='contrib-group fm-author')
            paper.authors += [e.string for e in authors_container.find_all('a')]

            paper.abstract = soup.find('h2', text='Abstract').next_sibling.string

            ref_container = soup.find('ul', class_='back-ref-list')
            for e in ref_container.select('li > span'):
                ref_string = ReferenceString(e.get_text())
                ref_string.journal = e.find('span', class_='ref-journal').string
                ref_string.volume = e.find('span', class_='ref-vol').string
                ref_string.pubmed_path = e.find('a').get('href')

                paper.references.append(ref_string)

    return paper
