import json
import pathlib

from utilities.json_labelling_utils import calculate_segmentation, calculate_area, generate_coco_bbox
from utilities.parser_utils import load_doc_instances
from .objects_categories import CATEGORIES, CATEGORIES_MAP
from pathlib import Path, PurePosixPath


def generate_json_labels(pickle_file, png_path):
    """
    Convert annotations from parsing pipeline to COCO annotation, in order to use GANs
    :param pickle_file: contains the dict with all the papers and the objects inside them
    :param png_path: path to generated png files (annotated via OpenCV)
    :return: train and validation json annotations
    """
    image_id = 1000000
    annotation_id = 2000000
    is_crowd = 0
    json_annotations = {"train": {"images": [], "annotations": [], "categories": {}},
                        "val": {"images": [], "annotations": [], "categories": {}}}
    docs_instances = load_doc_instances(pickle_file)
    papers_num = len(docs_instances.keys())
    train_papers_num = int(papers_num / 100 * 90)
    # for paper_key in ["5KGUvlXI6pKGkLqBu3YZ5", "1DW2ueDjdXU6kHDZq0Tg3z", "622U0zHbbvLmKLHzTHo6gZ"]:
    for paper_idx, paper_key in enumerate(docs_instances):
        key = "train" if paper_idx < train_papers_num else "val"
        title = docs_instances.get(paper_key).get("title")
        abstract = docs_instances.get(paper_key).get("abstract")
        # Save images for a key (paper)
        for page_idx, page_img_path in enumerate(Path(png_path).rglob(f'{paper_key}_*.png')):
            parts = page_img_path.parts
            page_img_path = PurePosixPath(pathlib.Path(*parts[2:]))
            json_annotations[key]["images"].append(
                {
                    "file_name": page_img_path.__str__(),
                    "height": 792,
                    "id": image_id,
                    "width": 612,
                })
            # Save annotations for the first page (title and abstract, for the moment)
            if page_idx == 0:
                if title:
                    json_annotations[key]["annotations"].append(
                        {
                            "segmentation": calculate_segmentation(title.get("coords")),
                            "area": calculate_area(title.get("coords")),
                            "is_crowd": is_crowd,
                            "image_id": image_id,
                            "bbox": generate_coco_bbox(title.get("coords")),
                            "category_id": CATEGORIES_MAP.get("title"),
                            "id": annotation_id
                        }
                    )
                    annotation_id += 1
                if abstract:
                    json_annotations[key]["annotations"].append(
                        {
                            "segmentation": calculate_segmentation(abstract.get("coords")),
                            "area": calculate_area(abstract.get("coords")),
                            "is_crowd": is_crowd,
                            "image_id": image_id,
                            "bbox": generate_coco_bbox(abstract.get("coords")),
                            "category_id": CATEGORIES_MAP.get("abstract"),
                            "id": annotation_id
                        }
                    )
                    annotation_id += 1
            for category in docs_instances.get(paper_key).keys():
                # title and abstract already handled, since they have a different data structure
                if category not in ["title", "abstract"]:
                    # ann object is the annotated object for that page
                    ann_object = docs_instances.get(paper_key).get(category).get(page_idx + 1)
                    if ann_object:
                        for i in range(len(ann_object)):
                            coords = ann_object[i].get("coords")
                            json_annotations[key]["annotations"].append(
                                {
                                    "segmentation": calculate_segmentation(coords),
                                    "area": calculate_area(coords),
                                    "is_crowd": is_crowd,
                                    "image_id": image_id,
                                    "bbox": generate_coco_bbox(coords),
                                    "category_id": CATEGORIES_MAP.get(category),
                                    "id": annotation_id
                                }
                            )
                            annotation_id += 1
            image_id += 1
        print(f"Processed paper n°: {paper_key}")
    # Dump json file
    json_annotations["train"]["categories"] = CATEGORIES.get("categories")
    json_annotations["val"]["categories"] = CATEGORIES.get("categories")
    with open('train.json', 'w') as fp:
        json.dump(json_annotations["train"], fp)
    with open('val.json', 'w') as fp:
        json.dump(json_annotations["val"], fp)
