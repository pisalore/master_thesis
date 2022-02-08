from collections import namedtuple
import json
from pathlib import Path
from fpdf import FPDF

from utilities.parser_utils import load_doc_instances

TEXT_CATEGORIES = ["title", "authors", "subtitles", "keywords", "text", "abstract", ] #"captions"
# Use a namedtuple for better understanding how to access bounding boxes
Rectangle = namedtuple("Rectangle", "xmin ymin xmax ymax")
# Instantiate generated pdf directory
gen_pdfs = Path("generated_pdfs")
gen_pdfs.mkdir(mode=0o777, parents=False, exist_ok=True)

# Import generated text
gen_text_dict = load_doc_instances("../generators/generated_instances.pickle")
lgt_dir = Path("../lgt/01_28_2022_19_46_25/layout_10")

for idx, json_path in enumerate(lgt_dir.rglob("*.json.json")):
    with open(json_path) as jf:
        # Get annotations from json file
        annotations = json.load(jf).get("annotations")
        # Instantiate a FPDF object
        pdf = FPDF(unit="pt")
        pdf.add_page()
        for k, ann in annotations.items():
            ann_category = ann.get("category")
            if ann_category in TEXT_CATEGORIES:
                bbox = Rectangle(*ann.get("bbox"))
                # Current point is the upper left
                pdf.set_xy(bbox.xmin, bbox.ymin)
                # TODO: Map objects to fonts
                pdf.set_font('Arial', 'B', 16)
                width, heigth = bbox.xmax - bbox.xmin,  bbox.ymax - bbox.ymin
                pdf.cell(width, heigth, 'Hello World!')
        # Save the generated PDF file
        pdf.output(f'{gen_pdfs}/{idx}.pdf', 'F')
