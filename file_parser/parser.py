from pathlib import Path

import fitz
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTFigure, LTTextBoxHorizontal
from wrapt_timeout_decorator import timeout

from converters.pdf2image_converter import convert_pdf_2_images
from utilities.annotator import annotate_imgs
from .tei import TEIFile
from utilities.parser_utils import (are_similar, do_overlap, element_contains_authors, check_keyword,
                                    calc_coords_from_pdfminer, check_subtitles, get_table_per_page,
                                    get_coords_from_fitz_rect, count_pdf_pages)


@timeout(45)
def parse_doc(pdf_path, xml_path, annotations_path=None):
    """
    Parse a document, given its PDF and XML files. The XML must be obtained with Grobid https://grobid.readthedocs.io/
    pdfs and xmls must be in the same directory (ex: data/pdfs, data/xml). The files must correspond in paths.
    In first page we looking for title, abstract, authors and keywords. For authors and keywords we search in the first
    part of the page (0->300 pixels considering y axis) in order to avoid to count useless elements..
    We exploit PDFMiner and Grobid output.
    :param pdf_path: path to pdf
    :param xml_path: path to xml
    :param annotations_path: If not empty, the path where save annotated converted images from PDFs
    :return: a dict containing objects inside PDF and theirs bounding boxes.
    """
    tei = TEIFile(xml_path)
    doc_instances = {"title": {}, "subtitles": {"terms": [], "coords": []}, "authors": {"terms": [], "coords": []},
                     "abstract": {}, "keywords": {"terms": [], "coords": []}, "figures": {}, "tables": {},
                     "formulas": tei.formula, "text": {}}
    # Find tables and images using PyMuPDF
    # doc = fitz.open(pdf_path)
    # tables = {}
    # for page in doc:
    #     # page_idx = page.number + 1
    #     tables_in_page = get_table_per_page(page)
    #     if tables_in_page:
    #         tables[page.number + 1] = tables_in_page
    #     image_list = page.get_images(full=True)
    #     for image in image_list:
    #         if not doc_instances["figures"].get(page_idx):
    #             doc_instances["figures"][page_idx] = []
    #         doc_instances["figures"][page_idx].append(
    #             {"coords": get_coords_from_fitx_rect(page.get_image_bbox(image))})
    # doc_instances["tables"] = tables
    # Count number of pages of PDF: if it is 1, maybe it is not a paper to be processed
    num_pages = count_pdf_pages(pdf_path)
    # Parse file using XML and PDF information
    if num_pages > 1:
        for page_layout in extract_pages(pdf_path):
            for element in page_layout:
                if isinstance(element, LTTextBoxHorizontal):
                    in_authors, in_keywords = False, False
                    if page_layout.pageid == 1:
                        if not doc_instances.get("title") and are_similar(element.get_text(), tei.title):
                            doc_instances["title"] = {"content": tei.title,
                                                      "coords": calc_coords_from_pdfminer([element.bbox])}
                        elif tei.authors and element_contains_authors(tei.authors, element.get_text()) \
                                and element.bbox[1] > 300:
                            # I will calculate the true coordinates later
                            doc_instances["authors"]["coords"].append(element.bbox)
                            in_authors = True
                        elif not doc_instances.get("abstract") and are_similar(element.get_text(), tei.abstract):
                            doc_instances["abstract"] = {"content": tei.abstract,
                                                         "coords": calc_coords_from_pdfminer([element.bbox])}
                        elif tei.keywords and check_keyword(element.get_text(), tei.keywords) \
                                and doc_instances.get("abstract").get("coords"):
                            # I will calculate the true coordinates later
                            doc_instances["keywords"]["coords"].append(element.bbox)
                            in_keywords = True
                    if check_subtitles(element.get_text(), tei.subtitles):
                        if not doc_instances["subtitles"].get(page_layout.pageid):
                            doc_instances["subtitles"][page_layout.pageid] = []
                        doc_instances["subtitles"][page_layout.pageid].append(
                            {"coords": calc_coords_from_pdfminer([element.bbox])})
                    # simple text. Check for "fist pages" elements
                    elif ((doc_instances.get("title").get("coords") and doc_instances.get("authors").get("coords") and
                           doc_instances.get("abstract").get("coords") and doc_instances.get("keywords").get("coords") and
                           not (in_keywords or in_authors)) and page_layout.pageid == 1) or page_layout.pageid != 1:
                        formula_overlap, tables_overlap, abstract_overlap = False, False, False
                        if doc_instances.get("formulas").get(page_layout.pageid):
                            for f in doc_instances.get("formulas").get(page_layout.pageid):
                                if do_overlap(f.get("coords"), calc_coords_from_pdfminer([element.bbox])):
                                    formula_overlap = True
                        if doc_instances.get("tables").get(page_layout.pageid) and not formula_overlap:
                            for t in doc_instances.get("tables").get(page_layout.pageid):
                                if do_overlap(t.get("coords"), calc_coords_from_pdfminer([element.bbox])):
                                    tables_overlap = True
                        if not (formula_overlap or tables_overlap):
                            if doc_instances.get("abstract").get("coords") and do_overlap(
                                    doc_instances.get("abstract").get("coords"),
                                    calc_coords_from_pdfminer([element.bbox])):
                                abstract_overlap = True
                        if not (formula_overlap or tables_overlap or abstract_overlap):
                            if not doc_instances["text"].get(page_layout.pageid):
                                doc_instances["text"][page_layout.pageid] = []
                            doc_instances["text"][page_layout.pageid].append(
                                {"coords": calc_coords_from_pdfminer([element.bbox])})
                if isinstance(element, LTFigure):
                    if not doc_instances["figures"].get(page_layout.pageid):
                        doc_instances["figures"][page_layout.pageid] = []
                    doc_instances["figures"][page_layout.pageid].append(
                        {"coords": calc_coords_from_pdfminer([element.bbox])})

            doc_instances["keywords"]["terms"] = tei.keywords
            doc_instances["authors"]["terms"] = tei.authors
            doc_instances["subtitles"]["terms"] = tei.subtitles
            doc_instances["tables"] = tei.tables

    # Postprocessing
    # Calculate authors an keywords coordinates based on all the elements found during parsing process.
    doc_instances["keywords"]["coords"] = calc_coords_from_pdfminer(doc_instances["keywords"]["coords"])
    doc_instances["authors"]["coords"] = calc_coords_from_pdfminer(doc_instances["authors"]["coords"])

    # Check if figures and tables overlap
    for table_page in doc_instances["tables"].keys():
        not_tables = []
        if doc_instances["figures"].get(table_page):
            for table in doc_instances["tables"][table_page]:
                table_coords = table.get("coords")
                for image_page in doc_instances["figures"][table_page]:
                    fig_coords = image_page.get("coords")
                    if do_overlap(table_coords, fig_coords):
                        not_tables.append(table)
                        break
            doc_instances["tables"][table_page] = [t for t in doc_instances["tables"][table_page] if
                                                   t not in not_tables]

    if annotations_path:
        png_path = convert_pdf_2_images(annotations_path, Path(pdf_path))
        annotate_imgs(png_path, doc_instances, 1)
    return doc_instances
