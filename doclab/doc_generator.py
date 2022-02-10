from collections import namedtuple
import json
from pathlib import Path
from fpdf import FPDF

from utilities.parser_utils import load_doc_instances

TEXT_CATEGORIES = [
    "title",
    "authors",
    "subtitles",
    "keywords",
    "text",
    "abstract",
]  # "captions"
FONTS = {
    "title": {
        "fontname": "NimbusRomNo9L",
        "tff": "NimbusRomNo9L.ttf",
        "size": 20,
        "h": 15,
        "align": "C",
    },
    "abstract": {
        "fontname": "NimbusRomNo9LBold",
        "tff": "NimbusRomNo9LBold.ttf",
        "size": 8.5,
        "h": 10,
        "align": "L",
    },
}
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
        pdf = FPDF(unit="pt", format="Letter")
        for _, font in FONTS.items():
            pdf.add_font(font["fontname"], "", font["tff"], uni=True)
        pdf.add_page()
        for k, ann in annotations.items():
            ann_category = ann.get("category")
            if ann_category in ["title", "abstract"]:
                bbox = Rectangle(*ann.get("bbox"))
                font = FONTS.get(ann_category)
                # Current point is the upper left
                pdf.set_xy(bbox.xmin, bbox.ymin)
                pdf.set_font(font.get("fontname"), "", font.get("size"))
                width, heigth = bbox.xmax - bbox.xmin, bbox.ymax - bbox.ymin
                pdf.multi_cell(
                    w=width,
                    h=font.get("h"),
                    align=font.get("align"),
                    txt=gen_text_dict.get(ann_category)[2],
                )
        # Save the generated PDF file
        pdf.output(f"{gen_pdfs}/{idx}.pdf", "F")
