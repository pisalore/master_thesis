import json
import os.path
from pathlib import Path

from converters.objects_categories import CATEGORIES, CATEGORIES_MAP
from utilities.json_labelling_utils import (
    calculate_segmentation,
    calculate_area,
    generate_coco_bbox,
)

FILEPATH_PREFIX = (
    "/home/lpisaneschi/master_thesis/data/png/fully_annotated/generated_pdfs_png"
)
GENERATED_PNG_PATH = "../doclab/generated_pdfs_png"


def augment_dataset_with_lgt_annotations(
    lgt_annotations_dir, train_json_path, val_json_path):
    """
    Generate json files in COCO format from the annotations generated using LayoutTransformer
    and augment old dataset.
    This operation is needed in order to fine tune an X101 model and evaluate the whole work.
    :param train_json_path: The path to json file containing original training data
    :param val_json_path: The path to json file containing original validation data
    :param lgt_annotations_dir: The directory path containing oll the generated layouts
    """
    train_json_file = open(train_json_path)
    val_json_file = open(val_json_path)
    coco_annotations = {
        "train": json.load(train_json_file),
        "val": json.load(val_json_file),
    }

    annotation_id = 100000000
    layouts_num = sum(1 for x in Path(lgt_annotations_dir).rglob("*.json.json"))
    train_papers_num = int(layouts_num / 100 * 90)

    # Iterate on all the synthetic layouts annotations
    for page_idx, lgt_json_path in enumerate(Path(lgt_annotations_dir).rglob("*.json.json")):
        lgt_annotation = json.load(open(lgt_json_path))
        layout_id = lgt_annotation["layout_id"]
        if os.path.exists(f"{GENERATED_PNG_PATH}/{layout_id}_0.png"):
            key = "train" if page_idx < train_papers_num else "val"
            annotations = lgt_annotation["annotations"]
            # Add figures meta information
            coco_annotations[key]["images"].append(
                {
                    "file_name": f"{FILEPATH_PREFIX}/{layout_id}_0.png",
                    "id": layout_id,
                    "height": 792,
                    "width": 612,
                }
            )
            # Add annotations
            for k, annotation in annotations.items():
                ann_bbox, category_id, area, label = (
                    annotation["bbox"],
                    annotation["category_id"],
                    annotation["area"],
                    annotation["category"],
                )
                # There were some annotation errors during the automatic document generation; for this reason, some
                # bounding boxes are out of scale and must not be considered
                if ann_bbox[3] < 792:
                    coco_annotations[key]["annotations"].append(
                        {
                            "segmentation": calculate_segmentation(ann_bbox),
                            "area": area,
                            "is_crowd": 0,
                            "image_id": layout_id,
                            "bbox": generate_coco_bbox(ann_bbox),
                            "category_id": CATEGORIES_MAP.get(label),
                            "id": annotation_id,
                        }
                    )
                    annotation_id += 1

            print(f"{lgt_json_path} layout processed. N° {page_idx}")
    # Dump json file
    coco_annotations["train"]["categories"] = CATEGORIES.get("categories")
    coco_annotations["val"]["categories"] = CATEGORIES.get("categories")
    with open("../X101/synthetic_train.json", "w") as fp:
        json.dump(coco_annotations["train"], fp)
    with open("../X101/synthetic_val.json", "w") as fp:
        json.dump(coco_annotations["val"], fp)


augment_dataset_with_lgt_annotations(
    "../lgt/01_28_2022_19_46_25", "../X101/train.json", "../X101/val.json"
)
