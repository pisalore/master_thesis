from difflib import SequenceMatcher
from itertools import groupby

import fitz
import numpy as np
import pickle

from typing import List

from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdftypes import resolve1


def clean_string(string):
    """
    Return a string with only alphanumerical characters.
    :param string: The string to be cleaned
    :return: The cleaned string
    """
    return "".join(e for e in string if e.isalnum()).lower()


def are_similar(string_a, string_b, replace_element=None):
    """
    Check if two string are similar using SequenceMatcher
    :param string_a: first string to be compared
    :param string_b: second string to be compared
    :param replace_element: String element to be removed in string_a (PDFMiner element) string
    :return: the result of matching
    """
    if replace_element:
        string_a = string_a.replace(replace_element, "")
    string_a, string_b = clean_string(string_a), clean_string(string_b)
    if (
        SequenceMatcher(None, string_a, string_b).ratio() >= 0.70
        or SequenceMatcher(None, string_b, string_a).ratio() >= 0.70
    ):
        return True
    else:
        return False


def element_contains_authors(authors_list, text):
    """
    Author extraction specific task. Given an author list obtained from TEI parsing, check if a PDFMiner element
    contains some author. It is needed for bounding box retrieval.
    :param authors_list: List of authors obtained from xml
    :param text: PDFMiner element text
    :return: Check if author is contained in text
    """
    text = clean_string(text)
    for author in authors_list:
        author = clean_string(author)
        if author in text:
            return True
    return False


def check_keyword(keyword_element, tei_keywords):
    """
    Check if PDFMiner element text contain keyword obtained from XML.
    :param keyword_element: PDFMiner element text
    :param tei_keywords: List of TEI keywords
    :return: Check if keyword is contained in text
    """
    keyword_element = clean_string(keyword_element).replace("keywords", "")
    for tei_k in tei_keywords:
        tei_k = clean_string(tei_k)
        if tei_k in keyword_element and len(keyword_element) < 100:
            return True
    return False


def check_subtitles(element_text, head_list):
    """
    Check if an element text could correspond to a subtitles, individuated by grobid.
    :param element_text: PDFMiner element text
    :param head_list: list of heads obtained with grobid
    :return:
    """
    for head in head_list:
        if are_similar(clean_string(head), clean_string(element_text)):
            return True
    return False


def calc_coords_from_pdfminer(coords):
    """
    Convert PDFMiner coordinates in image coordinates (where origin in (0,0) upper left, x axis goes right and y axis
    goes down, both in positive manner)
    :param coords: List of tuple of coordinates (PDFMiner bbox)
    :return: a tuple contained the calculated element coordinates
    """
    if coords:
        coords_matrix = np.array([tuple for tuple in coords])
        _, _, xr, yl = coords_matrix.max(axis=0)
        xl, yr, _, _ = coords_matrix.min(axis=0)
        yl, yr = 792 - yl, 792 - yr
        area = float((xr - xl) * (yr - yl))
        return [xl, yl, xr, yr], area
    return None


def count_pdf_pages(filename):
    """
    Count pages of a PDF file.
    :param filename: the pdf file
    :return: number of pages in pdf file
    """
    file = open(filename, "rb")
    parser = PDFParser(file)
    document = PDFDocument(parser)
    return resolve1(document.catalog["Pages"])["Count"]


def get_coords_from_fitz_rect(coords: fitz.Rect):
    """
    :param coords: A fitx Rect object
    :return: a coords tuple
    """
    return coords.x0, coords.y0, coords.x1, coords.y1


# works fine with 3UMb6OEuGWlc0TM3RdgLEX
# does not work fine with 6ucFdKM3OGWkvwB94XOY9W (counts figures also)
def get_table_per_page(page: fitz.Page) -> List[fitz.Rect]:
    """
    Get the location of tables in page
    by finding horizontal lines with same length
    :param page: page object of pdf
    :return: rectangles that contain tables
    """

    # make a list of horizontal lines
    # each line is represented by y and length
    hor_lines = []
    paths = page.get_drawings()
    for p in paths:
        for item in p["items"]:
            if item[0] == "l":  # this is a line item
                p1 = item[1]  # start point
                p2 = item[2]  # stop point
                if p1.y == p2.y:  # line horizontal?
                    hor_lines.append((p1, p2, p2.x - p1.x))  # potential table delimiter

    # find whether table exists by number of lines with same length > 3
    table_rects = []
    # sort the list for ensuring the correct group by same keys
    hor_lines.sort(key=lambda x: x[2])
    # getting the top-left point and bottom-right point of table
    for k, g in groupby(hor_lines, key=lambda x: x[2]):
        g = list(g)
        if len(g) >= 3:  # number of lines of table will always >= 3
            # g.sort(key=lambda x: x[0])  # sort by y value

            top_left = g[0][0]
            bottom_right = g[-1][1]
            table_rects.append(
                {"coords": (top_left.x, top_left.y, bottom_right.x, bottom_right.y)}
            )
    if table_rects:
        return table_rects


def do_overlap(coords1, coords2):
    """
    Check if two rects overlap
    :param coords1: tuple of coordinates of first rectangle (xleft, yleft, xright, yright)
    :param coords2: tuple of coordinates of second rectangle (xleft, yleft, xright, yright)
    :return: bool result of the test
    """
    if (
        (coords1[0] >= coords2[2])
        or (coords1[2] <= coords2[0])
        or (coords1[3] <= coords2[1])
        or (coords1[1] >= coords2[3])
    ):
        return False
    else:
        return True


def adjust_overlapping_coordinates(generic_obj_coords, text_coords, threshold):
    """
    Adjust text coordinates (considering the y axis) when overlap occurs with a generic object.
    :param generic_obj_coords: coordinates of a generic object (such as abstract, formula or tables)
    :param text_coords: text object coordinates
    :param threshold: A threshold to be considered when adjusting text coordinates
    :return:
    """
    if text_coords[1] < generic_obj_coords[1] < text_coords[3]:
        text_coords[3] = generic_obj_coords[1] - threshold
    else:
        text_coords[1] = generic_obj_coords[3] + threshold
    return text_coords


def save_doc_instances(filename, doc_instances):
    """
    Pickle a dictionary of documents objects
    :param filename: The name of pickle file (with its extension .pickle)
    :param doc_instances: A dictionary of documents objects
    """
    with open(filename, "wb") as handle:
        pickle.dump(doc_instances, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_doc_instances(pickle_file):
    """
    Load the pickled dictionary of documents objects
    :param pickle_file: The pickle file path
    :return: The pickled dictionary
    """
    with open(pickle_file, "rb") as handle:
        return pickle.load(handle)
