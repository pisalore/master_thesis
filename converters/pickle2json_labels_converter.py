import json
import pathlib
from pathlib import Path, PurePosixPath

from utilities.parser_utils import load_doc_instances


def generate_json_labels(pickle_file, png_path):
    json_annotations = {"images": [], "annotations": []}
    docs_instances = load_doc_instances(pickle_file)
    for paper_key in docs_instances:
        for page_img_path in Path(png_path).rglob(f'{paper_key}_*.png'):
            parts = page_img_path.parts
            page_img_path = PurePosixPath(pathlib.Path(*parts[2:]))
            image_id = page_img_path.stem
            json_annotations["images"].append(
                {
                    "file_name": page_img_path.__str__(),
                    "heigth": 792,
                    "id": image_id,
                    "width": 612,
                })
    with open('train.json', 'w') as fp:
        json.dump(json_annotations, fp)
