import json
import pathlib
from .objects_categories import CATEGORIES
from pathlib import Path, PurePosixPath
import re

from utilities.parser_utils import load_doc_instances


# TODO: calculate segmentation, bbox and area
def generate_json_labels(pickle_file, png_path):
    annotation_id = 1000000
    json_annotations = {"images": [], "annotations": [], "categories": {}}
    docs_instances = load_doc_instances(pickle_file)
    for paper_key in docs_instances:
        is_crowd = 0
        title = docs_instances.get(paper_key).get("title")
        abstract = docs_instances.get(paper_key).get("abstract")
        # Save images for a key (paper)
        for idx, page_img_path in enumerate(Path(png_path).rglob(f'{paper_key}_*.png')):
            parts = page_img_path.parts
            page_img_path = PurePosixPath(pathlib.Path(*parts[2:]))
            image_id = int(re.sub('\D', '', page_img_path.stem))
            json_annotations["images"].append(
                {
                    "file_name": page_img_path.__str__(),
                    "heigth": 792,
                    "id": image_id,
                    "width": 612,
                })
            # Save annotations for the first page (title and abstract, for the moment)
            if idx == 0:
                if title:
                    json_annotations["annotations"].append(
                        {
                            "segmentation": [[]],
                            "area": 0,
                            "imaged_id": image_id,
                            "bbox": list(title.get("coords")),
                            "id": annotation_id
                        }
                    )
                    annotation_id += 1
                if abstract:
                    json_annotations["annotations"].append(
                        {
                            "segmentation": [[]],
                            "area": 0,
                            "imaged_id": image_id,
                            "bbox": list(abstract.get("coords")),
                            "id": annotation_id
                        }
                    )
                    annotation_id += 1
            for category in docs_instances.get(paper_key).keys():
                # title and abstract already handled, since they have a different data structure
                if category not in ["title", "abstract"]:
                    # ann object is the annotated object for that page
                    ann_object = docs_instances.get(paper_key).get(category).get(idx + 1)
                    if ann_object:
                        json_annotations["annotations"].append(
                            {
                                "segmentation": [[]],
                                "area": 0,
                                "imaged_id": image_id,
                                "bbox": list(ann_object.get("coords")),
                                "id": annotation_id
                            }
                        )
                        annotation_id += 1

    # Dump json file
    json_annotations["categories"] = CATEGORIES.get("categories")
    with open('train.json', 'w') as fp:
        json.dump(json_annotations, fp)
