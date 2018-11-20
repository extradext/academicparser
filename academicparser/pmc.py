import dataclasses
import urllib.request
import urllib.parse
from typing import Optional

from bs4 import BeautifulSoup

from academicparser.model import Paper, PaperType, CitationString

REQUEST_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
PMC_PAPER_URL_FORMAT = 'https://www.ncbi.nlm.nih.gov/pmc/articles/{}/'

def parse(pmcid: str, parse_cite_string: bool = False) -> Optional[Paper]:
    paper = Paper(PaperType.PAPER_TYPE_PMC)
    paper.pmcid = pmcid

    paper_url: str = PMC_PAPER_URL_FORMAT.format(pmcid)

    req = urllib.request.Request(paper_url, headers={'User-Agent': REQUEST_USER_AGENT})
    with urllib.request.urlopen(req) as f:
        content_type = f.info()['Content-Type']
        charset = content_type.split(';')[-1].split('=')[-1]

        res_body = f.read().decode(charset)

        soup = BeautifulSoup(res_body, 'html.parser')
        paper.title = soup.find('h1', class_='content-title').string

        authors_container = soup.find('div', class_='contrib-group fm-author')
        paper.authors += [e.string for e in authors_container.find_all('a')]

        abstract_header = soup.find('h2', text='Abstract')
        if abstract_header is not None:
            abstract_container = abstract_header.parent.find('p')
            if abstract_container is not None:
                paper.abstract = abstract_container.string

        ref_container = soup.find('div', class_='ref-list-sec sec')
        sel_ref_container = ref_container.find('ul', class_='back-ref-list')

        if sel_ref_container is not None:
            ref_spans = sel_ref_container.select('li > span')
        else:
            ref_spans = ref_container.select('div > span')
        for e in ref_spans:
            citation_string_raw = e.get_text()
            citation_string_raw = citation_string_raw.replace(' [PubMed]', '').replace(' [PMC free article]', '')

            citation_string = CitationString(citation_string_raw)

            for a in e.find_all('a'):
                if a.string == 'PMC free article':
                    citation_string.pmc_free_article = a.get('href')
                elif a.string == 'PubMed':
                    citation_string.pubmed_path = a.get('href')

            paper.references.append(citation_string)

    if parse_cite_string:
        for r in paper.references:
            r.parse()

    return paper

