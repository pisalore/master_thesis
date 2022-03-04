import json
from pathlib import Path

from utilities.json_labelling_utils import calculate_segmentation, generate_coco_bbox
from converters.objects_categories import CATEGORIES_MAP, CATEGORIES
import xml.etree.ElementTree as ET

from detectron2.structures import BoxMode


def generate_json_labels(png_dir):
    """
    Generate json annotations (COCO format) to be used in X101 (ResNext), from xml annotations (Pascal VOC) obtained by
    manual correction.
    :param png_dir: The directory which contains the xml files
    """
    figures = ["figure-text", "figure"]
    image_id = 1000000
    annotation_id = 2000000
    is_crowd = 0
    json_annotations = {
        "train": [],
        "val": [],
    }
    pages_num = sum(1 for x in Path(png_dir).rglob("*.xml"))
    print(pages_num)
    train_papers_num = int(pages_num / 100 * 75)

    for page_idx, page_xml_path in enumerate(Path(png_dir).rglob("*.xml")):
        key = "train" if page_idx < train_papers_num else "val"
        tree = ET.parse(page_xml_path)
        root = tree.getroot()
        filename = page_xml_path.with_suffix(".png")
        annotations = []
        for obj in root.findall("object"):
            label = obj.find("name").text
            if label in figures:
                label = "figure"
            bbox = obj.find("bndbox")
            coords = (
                bbox.find("xmin").text,
                bbox.find("ymin").text,
                bbox.find("xmax").text,
                bbox.find("ymax").text,
            )
            coords = [float(c) for c in coords]
            annotations.append(
                {
                    "is_crowd": is_crowd,
                    "segmentation": calculate_segmentation(coords),
                    "bbox_mode": BoxMode.XYWH_ABS,
                    "bbox": generate_coco_bbox(coords),
                    "category_id": CATEGORIES_MAP.get(label),
                    "id": annotation_id,
                }
            )
            annotation_id += 1
        json_annotations[key].append(
            {
                "image_id": image_id,
                "file_name": str(filename),
                "height": 792,
                "width": 612,
                "annotations": annotations
            }
        )
        print(f"Processed image {filename} n°: {page_idx}")
        image_id += 1

        # Dump json file
        with open("/home/lpisaneschi/master_thesis/X101/train.json", "w") as fp:
            json.dump(json_annotations["train"], fp)
        with open("/home/lpisaneschi/master_thesis/X101/val.json", "w") as fp:
            json.dump(json_annotations["val"], fp)


def load_data(t="train"):
    if t == "train":
        with open("train.json", 'r') as file:
            train = json.load(file)
        return train
    elif t == "val":
      with open("val.json", 'r') as file:
          val = json.load(file)
    return val

# generate_json_labels("/home/lpisaneschi/master_thesis/data/png/fully_annotated")
