import random

from PyPDF2 import PdfFileWriter
from pylatex import Document, Alignat, TextBlock, NoEscape

from doclab.const import LATEX_FORMULA
from doclab.downloader import get_formula


def create_formula_pdf(filename, formulas):
    geometry_options = {"left": "0pt", "top": "0pt"}
    doc = Document(geometry_options=geometry_options, page_numbers=False)
    doc.change_length("\TPHorizModule", "1pt")
    doc.change_length("\TPVertModule", "1pt")

    for f in formulas:
        bbox = f.get("bbox")
        f_height = bbox[3] - bbox[1]
        n_eq = 1 if f_height < 30 else (int(f_height / 40))
        x_eq, y_eq = bbox[0], bbox[1]
        tot_height = 0
        for i in range(n_eq):
            with doc.create(TextBlock(0, x_eq, y_eq + tot_height)) as page:
                if tot_height + 40 < f_height:
                    agn = Alignat(numbering=False, escape=False)
                    agn.append(random.choice(LATEX_FORMULA))
                    page.append(agn)
                    tot_height += 40

    doc.generate_pdf(filename, clean_tex=True)


def merge_pdf_pages(page1, page2, out_filename):
    output = PdfFileWriter()
    page1.mergePage(page2)
    output.addPage(page1)
    with open(out_filename, "wb") as output_stream:
        output.write(output_stream)
