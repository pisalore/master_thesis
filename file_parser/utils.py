from difflib import SequenceMatcher
import pickle


def are_similar(string_a, string_b):
    string_a, string_b = ''.join(e for e in string_a if e.isalnum()), ''.join(e for e in string_b if e.isalnum())
    if SequenceMatcher(None, string_a, string_b).ratio() >= 0.70:
        return True


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


def load_doc_instances(pickle_file="doc_instances.pickle"):
    with open(pickle_file, 'rb') as handle:
        return pickle.load(handle)
