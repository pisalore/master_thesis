from difflib import SequenceMatcher
import numpy as np
import pickle


def are_similar(string_a, string_b):
    string_a, string_b = ''.join(e for e in string_a if e.isalnum()), ''.join(e for e in string_b if e.isalnum())
    if SequenceMatcher(None, string_a, string_b).ratio() >= 0.70:
        return True


def text_contains(text, element):
    text = ''.join(e for e in text if e.isalnum())
    element = ''.join(e for e in element if e.isalnum())
    return element in text


def element_contains_authors(authors_list, text):
    text = ''.join(e for e in text if e.isalnum())
    author_check = True
    for author in authors_list:
        author = ''.join(e for e in author if e.isalnum())
        author_check = author in text
    return author_check


def save_doc_instances(doc_instances):
    with open('docs_instances.pickle', 'wb') as handle:
        pickle.dump(doc_instances, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_doc_instances(pickle_file):
    with open(pickle_file, 'rb') as handle:
        return pickle.load(handle)


def check_keyword(keyword_element, tei_keywords):
    keyword_element = ''.join(e for e in keyword_element if e.isalnum()).replace("Keywords", "").lower()
    for tei_k in tei_keywords:
        tei_k = ''.join(e for e in tei_k if e.isalnum()).lower()
        if tei_k in keyword_element and len(keyword_element) < 200:
            return True
    return False


def calc_keywords_coords(coords):
    if coords:
        coords_matrix = np.array([tuple for tuple in coords])
        _, _, xr, yl = coords_matrix.max(axis=0)
        xl, yr, _, _ = coords_matrix.min(axis=0)
        yl, yr = 792 - yl, 792 - yr
        print((xl, yl, xr, yr))
        return xl, yl, xr, yr
    return None
