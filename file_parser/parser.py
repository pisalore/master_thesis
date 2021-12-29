from pathlib import Path
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTFigure, LTTextBoxHorizontal
from wrapt_timeout_decorator import timeout

from converters.pdf2image_converter import convert_pdf_2_images
from utilities.annotator import annotate_imgs
from .tei import TEIFile
from utilities.parser_utils import (are_similar, do_overlap, element_contains_authors, check_keyword,
                                    calc_coords_from_pdfminer, check_subtitles, adjust_overlapping_coordinates)


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
    # I use thiS data structure in order to find the title (if not in XML) by checking the text element font sizes and
    # considering the text with the bigger one.
    title_font = {"text": "", "font_size": 0, "coords": []}
    doc_instances = {"title": {}, "subtitles": tei.subtitles, "authors": {"terms": [], "coords": []},
                     "abstract": {}, "keywords": {"terms": [], "coords": []}, "figures": {}, "tables": tei.tables,
                     "formulas": tei.formula, "text": {}}
    # Parse file using XML and PDF information
    for page_layout in extract_pages(pdf_path):
        page_width = page_layout.width
        for element in page_layout:
            coords, area = calc_coords_from_pdfminer([element.bbox])
            if area > 600:
                if isinstance(element, LTTextBoxHorizontal):
                    in_authors, in_keywords = False, False
                    # I remove the noise derived from wrong annotations represented by little rectangles / objects
                    if page_layout.pageid == 1:
                        # I always save the element with the biggest font size of page 1: I will use it has title
                        # if there will be not match between grobid and pdfminer annotations for title
                        element_font_size = element._objs[0]._objs[0].size
                        if title_font.get("font_size") < float(element_font_size):
                            title_font["font_size"] = element_font_size
                            title_font["text"] = element.get_text()
                            title_font["coords"] = calc_coords_from_pdfminer([element.bbox])[0]
                        if tei.title and doc_instances.get("title") and are_similar(element.get_text(),
                                                                                    tei.title):
                            doc_instances["title"] = {"content": tei.title,
                                                      "coords": coords}
                        elif tei.authors and element_contains_authors(tei.authors, element.get_text()) \
                                and element.bbox[1] > 300:
                            # I will calculate the true coordinates later
                            doc_instances["authors"]["coords"].append(element.bbox)
                            in_authors = True
                        elif not doc_instances.get("abstract"):
                            if tei.abstract and are_similar(element.get_text(), tei.abstract, "Abstract"):
                                doc_instances["abstract"] = {"content": tei.abstract,
                                                             "coords": coords}
                            elif element.get_text().startswith("Abstract"):
                                doc_instances["abstract"] = {"content": element.get_text(),
                                                             "coords": calc_coords_from_pdfminer([element.bbox])[0]
                                                             }
                        elif tei.keywords and check_keyword(element.get_text(), tei.keywords) \
                                and doc_instances.get("abstract").get("coords"):
                            # I will calculate the true coordinates later
                            doc_instances["keywords"]["coords"].append(element.bbox)
                            in_keywords = True
                    if not check_subtitles(element.get_text(), tei.subtitles.get("titles_contents")):
                        # Simple text. Check for "first pages" elements, considering that title will be always present
                        if ((doc_instances.get("abstract").get("coords") and
                             not (in_keywords or in_authors)) and page_layout.pageid == 1) \
                                or page_layout.pageid != 1:
                            abstract_overlap = False
                            if doc_instances.get("formulas").get(page_layout.pageid):
                                # Since formula annotations come from GROBID,
                                # adjust text annotation if overlapping occurs.
                                for f in doc_instances.get("formulas").get(page_layout.pageid):
                                    if do_overlap(f.get("coords"), coords):
                                        adjust_overlapping_coordinates(f.get("coords"), coords, 20)
                            if page_layout.pageid == 1:
                                if doc_instances.get("abstract").get("coords") and do_overlap(
                                        doc_instances.get("abstract").get("coords"),
                                        coords):
                                    abstract_overlap = True
                            # It is impossible that, for any kind of annotation error, text overlaps abstract.
                            # If it happens, discard the text and maintain the abstract annotation.
                            if not abstract_overlap:
                                if (coords[2] - coords[0]) > page_width / 3:
                                    if not doc_instances["text"].get(page_layout.pageid):
                                        doc_instances["text"][page_layout.pageid] = []
                                    doc_instances["text"][page_layout.pageid].append(
                                        {"coords": coords})
                if isinstance(element, LTFigure):
                    if not doc_instances["figures"].get(page_layout.pageid):
                        doc_instances["figures"][page_layout.pageid] = []
                    doc_instances["figures"][page_layout.pageid].append(
                        {"coords": coords})

    doc_instances["keywords"]["terms"] = tei.keywords
    doc_instances["authors"]["terms"] = tei.authors
    doc_instances["subtitles"]["terms"] = tei.subtitles

    # Postprocessing
    # If title has not been found during parsing, I take the PDFMiner element of the first pae with the biggest font
    if not doc_instances["title"]:
        doc_instances["title"] = {"content": title_font["text"],
                                  "coords": title_font["coords"]}
    # Calculate authors an keywords coordinates based on all the elements found during parsing process.
    if doc_instances["keywords"]["coords"]:
        doc_instances["keywords"]["coords"] = calc_coords_from_pdfminer(doc_instances["keywords"]["coords"])[0]
    if doc_instances["authors"]["coords"]:
        doc_instances["authors"]["coords"] = calc_coords_from_pdfminer(doc_instances["authors"]["coords"])[0]

    # If figure and tables overlap -> discard table
    # If text and tables overlap -> discard text (since PDFMiner often annotates table content as text)
    for table_page in doc_instances["tables"].keys():
        not_tables, not_text = [], []
        for table in doc_instances["tables"][table_page]:
            table_coords = table.get("coords")
            if doc_instances["figures"].get(table_page):
                for image_page in doc_instances["figures"][table_page]:
                    fig_coords = image_page.get("coords")
                    if do_overlap(table_coords, fig_coords):
                        not_tables.append(table)
                        break
            if doc_instances["text"].get(table_page):
                for text in doc_instances["text"][table_page]:
                    text_coords = text.get("coords")
                    if do_overlap(table_coords, text_coords):
                        not_text.append(text)
        if doc_instances["tables"].get(table_page):
            doc_instances["tables"][table_page] = [t for t in doc_instances["tables"][table_page] if
                                                   t not in not_tables]
        if doc_instances["text"].get(table_page):
            doc_instances["text"][table_page] = [t for t in doc_instances["text"][table_page] if
                                                 t not in not_text]

    if annotations_path:
        png_path = convert_pdf_2_images(annotations_path, Path(pdf_path))
        annotate_imgs(png_path, doc_instances, 2)
    return doc_instances
