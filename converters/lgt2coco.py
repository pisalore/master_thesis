import json
import os.path
from pathlib import Path

from converters.objects_categories import CATEGORIES, CATEGORIES_MAP
from doclab.const import CORRECT_SIZE_IMAGES
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
    # images which annotations are incorrect on y-axis (for debug purposes)
    removed_images = []
    processed_training_imgs, processed_test_imgs = 0, 0

    annotation_id = 100000000
    layouts_num = sum(1 for x in Path(lgt_annotations_dir).rglob("*.json.json"))
    train_papers_num = int(layouts_num / 100 * 90)

    # Iterate on all the synthetic layouts annotations
    for page_idx, lgt_json_path in enumerate(Path(lgt_annotations_dir).rglob("*.json.json")):
        lgt_annotation = json.load(open(lgt_json_path))
        layout_id = lgt_annotation["layout_id"]
        if os.path.exists(f"{GENERATED_PNG_PATH}/{layout_id}_0.png"):
            key = "train" if page_idx < train_papers_num else "val"
            if key == "train":
                processed_training_imgs += 1
            else:
                processed_test_imgs += 1
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
                if layout_id not in CORRECT_SIZE_IMAGES:
                    # I need to re-compute bounding boxes considering image resizing (612x792) for those images which
                    # size was 596x842
                    ann_bbox = [ann_bbox[0] + 8, ann_bbox[1] - 25, ann_bbox[2] + 8, ann_bbox[3] - 25]
                # There were some annotation errors during the automatic document generation; for this reason, some
                # bounding boxes are out of scale and must not be considered
                if ann_bbox[1] > 0 and ann_bbox[3] < 792:
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
                else:
                    del coco_annotations[key]["images"][-1]
                    removed_images.append(layout_id)
                    if key == "train":
                        processed_training_imgs -= 1
                    else:
                        processed_test_imgs -= 1
                    break
            print(f"{lgt_json_path} layout processed. N° {page_idx}")
    # Dump json file
    coco_annotations["train"]["categories"] = CATEGORIES.get("categories")
    coco_annotations["val"]["categories"] = CATEGORIES.get("categories")
    with open("../X101/synthetic_train.json", "w") as fp:
        json.dump(coco_annotations["train"], fp)
    with open("../X101/synthetic_val.json", "w") as fp:
        json.dump(coco_annotations["val"], fp)
    with open("../X101/removed_images.txt", "w") as fp:
        for removed_img in removed_images:
            fp.write(f"{removed_img} \n")

    print(f"{processed_training_imgs + processed_test_imgs} processed: "
          f"{processed_training_imgs} for training "
          f"and {processed_test_imgs} for testing")


augment_dataset_with_lgt_annotations(
    "../lgt/01_28_2022_19_46_25", "../X101/train.json", "../X101/val.json"
)
