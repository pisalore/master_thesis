from pdfminer.high_level import extract_pages
from pdfminer.layout import LTFigure, LTTextBoxHorizontal

from wrapt_timeout_decorator import timeout

from .tei import TEIFile
from .utils import are_similar, element_contains_authors


@timeout(30)
def parse_doc(pdf_path, xml_path):
    tei = TEIFile(xml_path)
    doc_instances = {"title": {}, "authors": {}, "abstract": {}, "figures": []}
    for page_layout in extract_pages(pdf_path):
        for element in page_layout:
            if not doc_instances.get("abstract"):
                if isinstance(element, LTTextBoxHorizontal) and are_similar(element.get_text(), tei.abstract):
                    doc_instances["abstract"] = {"content": tei.abstract, "bbox": element.bbox}
            if not doc_instances.get("title"):
                if isinstance(element, LTTextBoxHorizontal) and are_similar(element.get_text(), tei.title):
                    doc_instances["title"] = {"content": tei.title, "bbox": element.bbox}
            if not doc_instances.get("authors"):
                if isinstance(element, LTTextBoxHorizontal) and element_contains_authors(tei.authors, element.get_text()):
                    doc_instances["authors"] = {"content": element.get_text(), "bbox": element.bbox}
            if isinstance(element, LTFigure):
                doc_instances.get("figures").append({"page": page_layout.pageid, "bbox": element.bbox})
    return doc_instances
