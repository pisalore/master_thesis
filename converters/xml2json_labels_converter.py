import json
from pathlib import Path

import xml.etree.ElementTree as ET

from converters.objects_categories import CATEGORIES_MAP, CATEGORIES
from utilities.json_labelling_utils import generate_coco_bbox, calculate_area, calculate_segmentation


def generate_json_labels(png_dir):
    """
    Generate json annotations (COCO format) to be used in GANs, from xml annotations (Pascal VOC)
    :param png_dir: The directory which contains the xml files
    """
    image_id = 1000000
    annotation_id = 2000000
    is_crowd = 0
    json_annotations = {"train": {"images": [],
                                  "annotations": [],
                                  "categories": {}
                                  },
                        "val": {"images": [],
                                "annotations": [],
                                "categories": {}
                                }
                        }
    pages_num = sum(1 for x in Path(png_dir).rglob('*.xml'))
    print(pages_num)
    train_papers_num = int(pages_num / 100 * 80)

    for page_idx, page_xml_path in enumerate(Path(png_dir).rglob('*.xml')):
        key = "train" if page_idx < train_papers_num else "val"
        tree = ET.parse(page_xml_path)
        root = tree.getroot()
        folder = root.find("folder").text
        filename = root.find("filename").text
        json_annotations[key]["images"].append(
            {
                "file_name": f"{folder}/{filename}",
                "height": 792,
                "id": image_id,
                "width": 612,
            })

        for obj in root.findall("object"):
            label = obj.find("name").text
            bbox = obj.find("bndbox")
            coords = bbox.find("xmin").text, bbox.find("ymin").text, bbox.find("xmax").text, bbox.find("ymax").text
            coords = [float(c) for c in coords]
            json_annotations[key]["annotations"].append(
                {
                    "segmentation": calculate_segmentation(coords),
                    "area": calculate_area(coords),
                    "is_crowd": is_crowd,
                    "image_id": image_id,
                    "bbox": generate_coco_bbox(coords),
                    "category_id": CATEGORIES_MAP.get(label),
                    "id": annotation_id
                }
            )
            annotation_id += 1
        print(f"Processed image {filename} n°: {page_idx}")
        image_id += 1

        # Dump json file
        json_annotations["train"]["categories"] = CATEGORIES.get("categories")
        json_annotations["val"]["categories"] = CATEGORIES.get("categories")
        with open('../../master_thesis/train.json', 'w') as fp:
            json.dump(json_annotations["train"], fp)
        with open('../../master_thesis/val.json', 'w') as fp:
            json.dump(json_annotations["val"], fp)


generate_json_labels("../data/png/ICDAR19a")
