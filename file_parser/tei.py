from bs4 import BeautifulSoup
from dataclasses import dataclass

from utilities.json_labelling_utils import calculate_area


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
        self.lxml_soup = self.read_tei(filename)
        self.xml_soup = self.read_tei(filename, markup="xml")
        self._text = None
        self._title = ""
        self._abstract = ""

    def read_tei(self, tei_file, markup="lxml"):
        with open(tei_file, "r", encoding="utf8") as tei:
            return BeautifulSoup(tei, features="xml")

    def elem_to_text(self, elem, default=""):
        if elem:
            return elem.getText()
        else:
            return default

    @property
    def doi(self):
        idno_elem = self.lxml_soup.find("idno", type="DOI")
        if not idno_elem:
            return ""
        else:
            return idno_elem.getText()

    @property
    def title(self):
        """
        :return: The paper title.
        """
        if not self._title:
            self._title = self.lxml_soup.title.getText()
        return self._title

    @property
    def abstract(self):
        """
        :return: The paper abstract
        """
        if not self._abstract:
            abstract = self.lxml_soup.abstract.getText(separator=" ", strip=True)
            self._abstract = abstract
        return self._abstract

    @property
    def keywords(self):
        """
        :return: The paper keywords
        """
        if self.lxml_soup.keywords:
            return [
                keyword.get_text()
                for keyword in self.lxml_soup.keywords.find_all("term")
            ]

    @property
    def authors(self):
        """
        :return: The paper authors
        """
        authors_in_header = self.lxml_soup.analytic.find_all("author")
        result = []
        for author in authors_in_header:
            persname = author.persname
            if not persname:
                continue
            firstname = self.elem_to_text(persname.find("forename", type="first"))
            middlename = self.elem_to_text(persname.find("forename", type="middle"))
            surname = self.elem_to_text(persname.surname)
            person = Person(firstname, middlename, surname)
            result.append(
                "{} {} {}".format(person.firstname, person.middlename, person.surname)
            )
        return result

    @property
    def emails(self):
        """
        :return: The authors' emails
        """
        authors_in_header = self.lxml_soup.analytic.find_all("author")
        result = []
        for author in authors_in_header:
            email = self.elem_to_text(author.email)
            if email:
                result.append(email)
        return result

    def get_authors_org(self, org_type):
        """
        Given the paper authors, search for organizations by organization type (such as laboratory, institution
        or department
        :param org_type: The organization type
        :return: A list of strings, representing organizations
        """
        authors_in_header = self.lxml_soup.analytic.find_all("author")
        result = []
        for author in authors_in_header:
            affiliations = author.find_all("affiliation")
            for affiliation in affiliations:
                org = self.elem_to_text(affiliation.find("orgname", type=org_type))
                if org and org not in result:
                    result.append(org)
        return result

    @property
    def text(self):
        """
        :return: The paper text
        """
        divs_text = []
        for div in self.lxml_soup.body.find_all("div"):
            # div is neither an appendix nor references, just plain text.
            if not div.get("type"):
                div_text = div.get_text(separator=" ", strip=True)
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
        for formula in self.lxml_soup.body.find_all("formula"):
            formula_coords = formula["coords"].split(",")
            page, xl, yl = (
                int(formula_coords[0]),
                float(formula_coords[1]),
                float(formula_coords[2]),
            )
            xr, yr = xl + float(formula_coords[3]), yl + float(formula_coords[4])
            coords = (xl, yl, xr, yr)
            area = calculate_area(coords)
            if not formulas.get(page):
                formulas[page] = []
            if 600 < area < 20000:
                formula = {
                    "formula_content": formula.get_text(),
                    "coords": (xl, yl, xr, yr),
                }
                formulas[page].append(formula)
        return formulas

    @property
    def tables(self):
        """
        :return: The paper tables
        """
        tables = {}
        for idx, table in enumerate(
            self.lxml_soup.body.find_all("figure", attrs={"type": "table"})
        ):
            table_coords = (
                table.table.get("coords").split(",")
                if table.table.get("coords")
                else table["coords"].split(",")
            )
            page, xl, yl = (
                int(table_coords[0]),
                float(table_coords[1]),
                float(table_coords[2]),
            )
            xr, yr = xl + float(table_coords[3]), yl + float(table_coords[4])
            coords = (xl, yl, xr, yr)
            area = calculate_area(coords)
            if not tables.get(page):
                tables[page] = []
            desc, table_content = None, None
            for content in table.contents:
                if content.name == "table":
                    table_content = content.text
                elif content.name == "figdesc":
                    desc = content.text
            if coords and area > 600:
                tables[page].append(
                    {
                        "id": idx,
                        "desc": desc,
                        "content": table_content,
                        "coords": coords,
                    }
                )
        return tables

    @property
    def subtitles(self):
        """
        :return: The subtitles of a paper, intended as the "head" tags.
        """
        subtitles = {"titles_contents": []}
        for idx, head in enumerate(self.xml_soup.find_all("head")):
            if head.get("coords"):
                multiline_title_coords = head.get("coords").split(";")
                for title in multiline_title_coords:
                    title_coords = title.split(",")
                    page, xl, yl = (
                        int(title_coords[0]),
                        float(title_coords[1]),
                        float(title_coords[2]),
                    )
                    xr, yr = xl + float(title_coords[3]), yl + float(title_coords[4])
                    area = float((xr - xl) * (yr - yl))
                    if area > 500:
                        if not subtitles.get(page):
                            subtitles[page] = []
                        subtitle = {
                            "title_content": head.get_text(),
                            "coords": (xl, yl, xr, yr),
                        }
                        subtitles[page].append(subtitle)
                        # this list is needed in order to compare simple text to titles and avoid overlapping during
                        # the annotation process
                        subtitles.get("titles_contents").append(head.get_text())
        return subtitles

    @property
    def references(self):
        """
        :return: references as a list. each reference is simplified, consisting only in authors and work title.
        """
        citations = []
        for idx, ref in enumerate(self.xml_soup.find_all("biblStruct")):
            if idx != 0:
                reference = f"[{idx}]    "
                analytic = ref.analytic
                monogr = ref.monogr
                if analytic:
                    title = analytic.title.get_text() if analytic.title else ""
                    for author in ref.analytic.find_all("author"):
                        persname = author.persName
                        if persname:
                            first_name = persname.forename.get_text() if persname.forename else ""
                            surname = persname.surname.get_text() if persname.surname else ""
                            if persname.forename and persname.surname:
                                reference += f"{first_name} {surname}, "
                    if title:
                        reference += f"\n        \"{title}\""
                if monogr:
                    title = monogr.title.get_text() if monogr.title else ""
                    meeting = monogr.meeting.get_text() if monogr.meeting else ""
                    if title:
                        reference += f" in {title}"
                    elif meeting:
                        reference += f" in {meeting}"
                if len(reference) > 10:
                    citations.append(reference)
        return citations

