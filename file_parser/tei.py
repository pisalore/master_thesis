from bs4 import BeautifulSoup
from dataclasses import dataclass


@dataclass
class Person:
    firstname: str
    middlename: str
    surname: str


class TEIFile(object):
    """
    A wrapprer class for XML TEI files handling, using BeautifulSoup.
    """

    def __init__(self, filename):
        self.filename = filename
        self.soup = self.read_tei(filename)
        self._text = None
        self._title = ''
        self._abstract = ''

    def read_tei(self, tei_file):
        with open(tei_file, 'r', encoding="utf8") as tei:
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
        """
        :return: The paper title.
        """
        if not self._title:
            self._title = self.soup.title.getText()
        return self._title

    @property
    def abstract(self):
        """
        :return: The paper abstract
        """
        if not self._abstract:
            abstract = self.soup.abstract.getText(separator=' ', strip=True)
            self._abstract = abstract
        return self._abstract

    @property
    def keywords(self):
        """
        :return: The paper keywords
        """
        if self.soup.keywords:
            return [keyword.get_text() for keyword in self.soup.keywords.find_all("term")]

    @property
    def authors(self):
        """
        :return: The paper authors
        """
        authors_in_header = self.soup.analytic.find_all('author')
        result = []
        for author in authors_in_header:
            persname = author.persname
            if not persname:
                continue
            firstname = self.elem_to_text(
                persname.find("forename", type="first"))
            middlename = self.elem_to_text(
                persname.find("forename", type="middle"))
            surname = self.elem_to_text(persname.surname)
            person = Person(firstname, middlename, surname)
            result.append("{} {} {}".format(person.firstname,
                                            person.middlename, person.surname))
        return result

    @property
    def text(self):
        """
        :return: The paper text
        """
        divs_text = []
        for div in self.soup.body.find_all("div"):
            # div is neither an appendix nor references, just plain text.
            if not div.get("type"):
                div_text = div.get_text(separator=' ', strip=True)
                divs_text.append(div_text)

        plain_text = " ".join(divs_text)
        self._text = plain_text
        return self._text

    @property
    def formula(self):
        """
        :return: The paper formulas and algorithms
        """
        formulas = {}
        for formula in self.soup.body.find_all("formula"):
            formula_coords = formula["coords"].split(",")
            page, xl, yl = int(formula_coords[0]), float(formula_coords[1]), float(formula_coords[2])
            xr, yr = xl + float(formula_coords[3]), yl + float(formula_coords[4])
            if not formulas.get(page):
                formulas[page] = []
            formula = {"formula_content": formula.get_text(),
                       "coords": (xl, yl,  xr, yr)}
            formulas[page].append(formula)
        return formulas

    @property
    def tables(self):
        """
        :return: The paper tables
        """
        tables = {}
        for idx, table in enumerate(self.soup.body.find_all("figure", attrs={"type": "table"})):
            table_coords = table["coords"].split(",")
            page, xl, yl = int(table_coords[0]), float(table_coords[1]), float(table_coords[2])
            xr, yr = xl + float(table_coords[3]), yl + float(table_coords[4])
            coords = (xl, yl, xr, yr)
            if not tables.get(page):
                tables[page] = []
            desc, table_content = None, None
            for content in table.contents:
                if content.name == "table":
                    table_content = content.text
                elif content.name == "figdesc":
                    desc = content.text
            if desc and table_content and coords:
                tables[page].append({"id": idx, "desc": desc,
                                     "content": table_content, "coords": coords})
        return tables
