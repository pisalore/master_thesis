from difflib import SequenceMatcher
import numpy as np
import pickle


def clean_string(string):
    """
    Return a string with only alphanumerical characters.
    :param string: The string to be cleaned
    :return: The cleaned string
    """
    return ''.join(e for e in string if e.isalnum()).lower()


def are_similar(string_a, string_b):
    """
    Check if two string are similar using SequenceMatcher
    :param string_a: first string to be compared
    :param string_b: second string to be compared
    :return: the result of matching
    """
    string_a, string_b = clean_string(string_a), clean_string(string_b)
    if SequenceMatcher(None, string_a, string_b).ratio() >= 0.70:
        return True


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
    keyword_element = clean_string(keyword_element).replace("Keywords", "")
    for tei_k in tei_keywords:
        tei_k = clean_string(tei_k)
        if tei_k in keyword_element and len(keyword_element) < 200:
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
        print((xl, yl, xr, yr))
        return xl, yl, xr, yr
    return None


def save_doc_instances(doc_instances):
    """
    Pickle a dictionary of documents objects
    :param doc_instances: A dictionary of documents objects
    """
    with open('docs_instances.pickle', 'wb') as handle:
        pickle.dump(doc_instances, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_doc_instances(pickle_file):
    """
    Load the pickled dictionary of documents objects
    :param pickle_file: The pickle file path
    :return: The pickled dictionary
    """
    with open(pickle_file, 'rb') as handle:
        return pickle.load(handle)
