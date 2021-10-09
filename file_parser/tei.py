from bs4 import BeautifulSoup
from dataclasses import dataclass


@dataclass
class Person:
    firstname: str
    middlename: str
    surname: str


class TEIFile(object):
    def __init__(self, filename):
        self.filename = filename
        self.soup = self.read_tei(filename)
        self._text = None
        self._title = ''
        self._abstract = ''

    def read_tei(self, tei_file):
        with open(tei_file, 'r',  encoding="utf8") as tei:
            return BeautifulSoup(tei, 'lxml')

    def elem_to_text(self, elem, default=''):
        if elem:
            return elem.getText()
        else:
            return default

    @property
    def doi(self):
        idno_elem = self.soup.find('idno', type='DOI')
        if not idno_elem:
            return ''
        else:
            return idno_elem.getText()

    @property
    def title(self):
        if not self._title:
            self._title = self.soup.title.getText()
        return self._title

    @property
    def abstract(self):
        if not self._abstract:
            abstract = self.soup.abstract.getText(separator=' ', strip=True)
            self._abstract = abstract
        return self._abstract

    @property
    def authors(self):
        authors_in_header = self.soup.analytic.find_all('author')

        result = []
        for author in authors_in_header:
            persname = author.persname
            if not persname:
                continue
            firstname = self.elem_to_text(persname.find("forename", type="first"))
            middlename = self.elem_to_text(persname.find("forename", type="middle"))
            surname = self.elem_to_text(persname.surname)
            person = Person(firstname, middlename, surname)
            result.append("{} {} {}".format(person.firstname, person.middlename, person.surname))
        return result

    @property
    def text(self):
        divs_text = []
        for div in self.soup.body.find_all("div"):
            # div is neither an appendix nor references, just plain text.
            if not div.get("type"):
                div_text = div.get_text(separator=' ', strip=True)
                divs_text.append(div_text)

        plain_text = " ".join(divs_text)
        self._text = plain_text
        return self._text