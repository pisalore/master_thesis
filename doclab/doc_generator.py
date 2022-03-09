import os
import random
from collections import namedtuple
import json
from pathlib import Path

from PyPDF2 import PdfFileReader
from fpdf import FPDF
from wrapt_timeout_decorator import timeout

from converters.pdf2image_converter import convert_pdf_2_images
from doclab.const import FONTS, ORGS, IMAGE_CATEGORIES, TEXT_CATEGORIES
from doclab.downloader import get_image
from doclab.tex_converter import create_formula_pdf, merge_pdf_pages
from utilities.parser_utils import load_doc_instances

# Use a namedtuple for better understanding how to access bounding boxes
Rectangle = namedtuple("Rectangle", "xmin ymin xmax ymax")
# Instantiate generated pdf directory
gen_pdfs = Path("generated_pdfs")
png_dir = Path("generated_pdfs_png")
gen_pdfs.mkdir(mode=0o777, parents=False, exist_ok=True)
png_dir.mkdir(mode=0o777, parents=False, exist_ok=True)


# Import generated text
gen_text_dict = load_doc_instances("../generators/generated_instances_rev3.pickle")
lgt_dir = Path("../lgt/01_28_2022_19_46_25/")


def get_formula_annotations(annotations):
    formulas = []
    for _, v in annotations.items():
        if v["category"] == "formula":
            formulas.append(v)
    return formulas


@timeout(45)
def generate_document(pdf, json_path, filename, out_filepath):
    print(f"Generating PDF from {json_path}...")
    # output formulas filename (without .pdf) if a layout contains formula annotations
    formulas_path = f"temp/formulas{filename}"
    contains_formula = False
    with open(json_path) as jf:
        # Get annotations from json file
        annotations = json.load(jf).get("annotations")
        formulas = get_formula_annotations(annotations)
        if formulas:
            contains_formula = True
            create_formula_pdf(formulas_path, formulas)
        # Iterate over all annotations
        for k, ann in annotations.items():
            bbox = Rectangle(*ann.get("bbox"))
            ann_category = ann.get("category")
            if ann.get("area") > 5000 or ann_category in TEXT_CATEGORIES:
                if ann_category in TEXT_CATEGORIES:
                    # Get correct coordinates and font
                    font = FONTS.get(ann_category)
                    pdf.set_font(font.get("fontname"), "", font.get("size"))
                    width, height = bbox.xmax - bbox.xmin, bbox.ymax - bbox.ymin
                    # Given the generated text, split it in text rows, for correct pagination
                    cell_kwargs = {
                        "w": width,
                        "h": font.get("h"),
                        "align": font.get("align"),
                    }
                    # Get splitted text rows
                    # if I am deliang with captions, I want to take generated text from the "text" category
                    ann_category = (
                        "text" if ann_category == "caption" else ann_category
                    )
                    texts = gen_text_dict.get(ann_category)
                    text_rows = pdf.multi_cell(
                        **cell_kwargs,
                        txt=texts[random.randrange(len(texts))],
                        split_only=True,
                    )
                    if ann_category == "authors":
                        for line in [
                            ORGS[random.randrange(len(ORGS))],
                            "emails",
                        ]:
                            texts = gen_text_dict.get(line)
                            txt = texts[random.randrange(len(texts))]
                            if line == "emails":
                                start = random.randrange(len(texts))
                                txt = ", ".join(texts[start : start + 2])
                            text_rows += pdf.multi_cell(
                                **cell_kwargs,
                                txt=txt,
                                split_only=True,
                            )
                    if ann_category in ["text", "abstract", "references"]:
                        for i in range(100):
                            txt = texts[random.randrange(len(texts))]
                            text_rows += pdf.multi_cell(
                                **cell_kwargs,
                                txt=txt,
                                split_only=True,
                            )
                    # Write on PDF. ret_y defines the y of each cell and will be updated according to text height.
                    # h height is an accumulator: if the rows' height exceeds the bbox height, writing process is stopped.
                    # It applies only to "text categories"

                    ret_y = bbox.ymin
                    acc_height = 0
                    for txt in text_rows:
                        # I don't want to add text if I overcome the pdf max height
                        if acc_height <= height:
                            pdf.set_xy(bbox.xmin, ret_y)
                            pdf.multi_cell(**cell_kwargs, txt=txt)
                            ret_y += font.get("h")
                            acc_height += font.get("h")
                        else:
                            break
                elif ann_category in IMAGE_CATEGORIES.keys():
                    visi_img_category = IMAGE_CATEGORIES[ann_category]
                    xmin, xmax, width = (
                        bbox.xmin,
                        bbox.xmax,
                        int(bbox.xmax - bbox.xmin),
                    )
                    ymin, ymax, height = (
                        bbox.ymin,
                        bbox.ymax,
                        int(bbox.ymax - bbox.ymin),
                    )
                    try:
                        img = get_image(width, height, visi_img_category)
                        pdf.image(img, xmin, ymin, width, height, "PNG")
                        # remove the image
                        os.remove(img)
                    except:
                        pass

        if contains_formula:
            # If annotations contain formula, I have to merge two PDF: one containing the formulas written using LateX
            # and the one written with FPDF

            # save FPDF file
            pdf.output(f"temp/{filename}_temp.pdf", "F")
            # Open FPDF file and Formulas file using PyPDF2 PdfFileReader
            with open(f"temp/{filename}_temp.pdf", "rb") as f1:
                fpdf_pdf = PdfFileReader(f1)
                with open(f"{formulas_path}.pdf", "rb") as f2:
                    formula_pdf = PdfFileReader(f2)
                    # Merge the pages contents (each PDF file is always formed by one page) and output the final result
                    merge_pdf_pages(
                        formula_pdf.getPage(0),
                        fpdf_pdf.getPage(0),
                        out_filepath,
                    )
            # Remove useless intermediate file
            os.remove(f"temp/{filename}_temp.pdf")
            os.remove(f"temp/formulas{filename}.pdf")
        else:
            # Otherwise, simply output the FPDF file
            pdf.output(out_filepath, "F")
        if not os.path.exists(png_dir.joinpath(f"{filename}_0.png")):
            convert_pdf_2_images(png_dir, Path(out_filepath))


def generate_synthetic_documents():
    for idx, json_path in enumerate(lgt_dir.rglob("*.json.json")):
        try:
            # Instantiate pdf object (fpdf)
            pdf = FPDF(unit="pt")
            pdf.add_page()
            # Add all necessary fonts for each type of text (titles, subtitles, abstract, authors...) to let them
            # available during documents writing
            for _, font in FONTS.items():
                pdf.add_font(font["fontname"], "", font["tff"], uni=True)
            filename = json_path.stem.split(".json")[0]
            # output file path
            out_filepath = f"{gen_pdfs}/{filename}.pdf"
            if not os.path.exists(out_filepath):
                generate_document(pdf, json_path, filename, out_filepath)
        except TimeoutError as err:
            print("TimeOut error. Continue.")


if __name__ == "__main__":
    generate_synthetic_documents()
