import random
from collections import namedtuple
import json
from pathlib import Path
from fpdf import FPDF

from doclab.const import FONTS, ORGS
from utilities.parser_utils import load_doc_instances

# Use a namedtuple for better understanding how to access bounding boxes
Rectangle = namedtuple("Rectangle", "xmin ymin xmax ymax")
# Instantiate generated pdf directory
gen_pdfs = Path("generated_pdfs")
gen_pdfs.mkdir(mode=0o777, parents=False, exist_ok=True)

# Import generated text
gen_text_dict = load_doc_instances("../generators/generated_instances_rev2.pickle")
lgt_dir = Path("../lgt/01_28_2022_19_46_25/layout_10")

for idx, json_path in enumerate(lgt_dir.rglob("*.json.json")):
    # Instantiate a FPDF object and add a page (only one is needed, since a generated layout
    # corresponds to one page)
    pdf = FPDF(unit="pt")
    pdf.add_page()
    with open(json_path) as jf:
        # Get annotations from json file
        annotations = json.load(jf).get("annotations")
        # Add all necessary fonts for each type of text (titles, subtitles, abstract, authors...) to let them available
        # during documents writing
        for _, font in FONTS.items():
            pdf.add_font(font["fontname"], "", font["tff"], uni=True)
        # Iterate over all annotations
        for k, ann in annotations.items():
            ann_category = ann.get("category")
            if ann_category in ["title", "authors", "abstract", "text", "subtitle"]:
                # Get correct coordinates and font
                bbox = Rectangle(*ann.get("bbox"))
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
                texts = gen_text_dict.get(ann_category)
                text_rows = pdf.multi_cell(
                    **cell_kwargs,
                    txt=texts[random.randrange(len(texts))],
                    split_only=True,
                )
                if ann_category == "authors":
                    for line in [ORGS[random.randrange(len(ORGS))], "emails"]:
                        texts = gen_text_dict.get(line)
                        txt = texts[random.randrange(len(texts))]
                        if line == "emails":
                            start = random.randrange(len(texts))
                            txt = ", ".join(texts[start : start + 2])
                        text_rows += pdf.multi_cell(
                            **cell_kwargs, txt=txt, split_only=True,
                        )
                if ann_category in ["text", "abstract"]:
                    for i in range(100):
                        txt = texts[random.randrange(len(texts))]
                        text_rows += pdf.multi_cell(
                            **cell_kwargs,
                            txt=texts[random.randrange(len(texts))],
                            split_only=True,
                        )
                # Write on PDF. ret_y defines the y of each cell and will be updated according to text height.
                # h height is an accumulator: if the rows' height exceeds the bbox height, writing process is stopped.
                ret_y = bbox.ymin
                acc_height = 0
                for txt in text_rows:
                    if acc_height <= height:
                        pdf.set_xy(bbox.xmin, ret_y)
                        pdf.multi_cell(**cell_kwargs, txt=txt)
                        ret_y += font.get("h")
                        acc_height += font.get("h")
                    else:
                        break
        # Save the generated PDF file
        pdf.output(f"{gen_pdfs}/{idx}.pdf", "F")
