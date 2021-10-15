from pathlib import Path

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTFigure, LTTextBoxHorizontal
from wrapt_timeout_decorator import timeout

from converters.pdf2image_converter import convert_pdf_2_images
from utilities.annotator import annotate_imgs
from .tei import TEIFile
from utilities.parser_utils import are_similar, element_contains_authors, check_keyword, calc_coords_from_pdfminer


@timeout(30)
def parse_doc(pdf_path, xml_path, annotations_path=None):
    """
    Parse a document, given its PDF and XML files. The XML must be obtained with Grobid https://grobid.readthedocs.io/
    pdfs and xmls must be in the same directory (ex: data/pdfs, data/xml). The files must correspond in paths.
    In first page we looking for title, abstract, authors and keywords. For authors and keywords we search in the first
    part of the page (0->300 pixels considering y axis) in order to avoid to count useless elements..
    We exploit PDFMiner and Grobid output.
    :param pdf_path: path to pdfs
    :param xml_path: path to xmls
    :param annotations_path: If not empty, the path where save annotated converted images from PDFs
    :return: a dict containing objects inside PDF and theirs bounding boxes.
    """
    tei = TEIFile(xml_path)
    doc_instances = {"title": {},
                     "authors": {"terms": [], "coords": []},
                     "abstract": {},
                     "keywords": {"terms": [], "coords": []},
                     "figures": {},
                     "tables": [],
                     "formulas": []}
    for page_layout in extract_pages(pdf_path):
        for element in page_layout:
            if isinstance(element, LTTextBoxHorizontal):
                if page_layout.pageid == 1:
                    if not doc_instances.get("title") and are_similar(element.get_text(), tei.title):
                        doc_instances["title"] = {"content": tei.title,
                                                  "coords": calc_coords_from_pdfminer([element.bbox])}
                    elif tei.authors and element_contains_authors(tei.authors, element.get_text()) \
                            and element.bbox[1] > 300:
                        doc_instances["authors"]["coords"].append(element.bbox)
                    elif not doc_instances.get("abstract") and are_similar(element.get_text(), tei.abstract):
                        doc_instances["abstract"] = {"content": tei.abstract,
                                                     "coords": calc_coords_from_pdfminer([element.bbox])}
                    elif tei.keywords and check_keyword(element.get_text(), tei.keywords) \
                            and element.bbox[1] > 300:
                        doc_instances["keywords"]["coords"].append(element.bbox)
            if isinstance(element, LTFigure):
                if not doc_instances["figures"].get(page_layout.pageid):
                    doc_instances["figures"][page_layout.pageid] = []
                doc_instances["figures"][page_layout.pageid].append({"coords": calc_coords_from_pdfminer([element.bbox])})

        doc_instances["tables"] = tei.tables
        doc_instances["formulas"] = tei.formula
        doc_instances["keywords"]["terms"] = tei.keywords
        doc_instances["authors"]["terms"] = tei.authors

    # Postprocessing
    doc_instances["keywords"]["coords"] = calc_coords_from_pdfminer(doc_instances["keywords"]["coords"])
    doc_instances["authors"]["coords"] = calc_coords_from_pdfminer(doc_instances["authors"]["coords"])

    if annotations_path:
        png_path = convert_pdf_2_images(annotations_path, Path(pdf_path))
        annotate_imgs(png_path, doc_instances, 1)
    return doc_instances
