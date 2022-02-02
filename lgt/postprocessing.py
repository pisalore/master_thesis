import json
from collections import namedtuple
from pathlib import Path, PurePosixPath

from PIL import Image, ImageDraw, ImageOps

from converters.objects_categories import CATEGORIES_MAP, COLORS_MAP
from utilities.json_labelling_utils import calculate_area


def do_rects_overlap(rect1, rect2):
    """
    Check if two rects in form (x1, y1, x2, y2) do overlap.
    """
    Rectangle = namedtuple("Rectangle", "xmin ymin xmax ymax")
    rect1 = Rectangle(*rect1)
    rect2 = Rectangle(*rect2)
    dx = min(rect1.xmax, rect2.xmax) - max(rect1.xmin, rect2.xmin)
    dy = min(rect1.ymax, rect2.ymax) - max(rect1.ymin, rect2.ymin)
    if (dx >= 0) and (dy >= 0):
        return True
    return False


def merge_rects(rect1, rect2):
    Rectangle = namedtuple("Rectangle", "x1 y1 x2 y2")
    rect1 = Rectangle(*rect1)
    rect2 = Rectangle(*rect2)
    return [
        min(rect1.x1, rect2.x1),
        min(rect1.y1, rect2.y1),
        max(rect1.x2, rect2.x2),
        max(rect1.y2, rect2.y2),
    ]


def clean_generated_layouts(layouts_dir):
    """
    Clean the generated layouts sampled from LayoutTransformer model.
    A layout is intended to be a single document page.
    :param layouts_dir: The directory containing all generated layouts
    :return: The cleaned layouts
    """
    for idx, layout in enumerate(Path(layouts_dir).rglob("*.json")):
        categorized_data = {}
        with open(layout) as f:
            layout_data = json.load(f)
            annotations = layout_data.get("annotations")
            filename = layout_data["filename"]
            # save annotations occurrences belonging to the same category
            for k, o in annotations.items():
                category = o.get("category")
                if not categorized_data.get(category):
                    categorized_data[category] = {}
                categorized_data[category][k] = {"instance": o, "overlaps_with": []}
            # for each instance, save objects' id with which it does overlap
            for _, category_objs in categorized_data.items():
                for k1, o1 in category_objs.items():
                    overlaps = []
                    for k2, o2 in category_objs.items():
                        if k2 != k1:
                            if do_rects_overlap(
                                o1["instance"].get("bbox"), o2["instance"].get("bbox")
                            ):
                                overlaps.append(k2)
                    o1["overlaps_with"] = overlaps
            # create merge lists
            merge = {}
            for _, category_objs in categorized_data.items():
                # take the category from the first category objects dictionary
                # and instantiate the merge list for that category
                category = list(category_objs.values())[0]["instance"]["category"]
                merge[category] = []
                # for each instance of a category, check intersections with all the other instances' overlap lists
                for k1, o1 in category_objs.items():
                    merge_list = [k1]
                    for k2, o2 in category_objs.items():
                        if k2 != k1 and k2 in o1.get("overlaps_with"):
                            merge_list = [*merge_list, *o2.get("overlaps_with"), k2]
                    # create distinct overlap lists
                    merge[category].append(list(set(merge_list)))
                merge[category] = [
                    list(x) for x in set(tuple(x) for x in merge[category])
                ]
            # TODO: uniqueness in lists ids
            postprocessed_layout = {
                "filename": filename,
                "layout_id": layout_data["layout_id"],
                "annotations": {},
            }
            annotation_id = 0
            for category, values in merge.items():
                for keys in values:
                    # CASE 1: Single rect which does not overlap with any other rect
                    if len(keys) == 1:
                        postprocessed_layout["annotations"][
                            annotation_id
                        ] = annotations[keys[0]]
                    else:
                        keys_it = iter(keys)
                        merged_rect = None
                        for k_id in keys_it:
                            rect1 = annotations[k_id].get("bbox")
                            try:
                                rect2 = annotations[next(keys_it)].get("bbox")
                                m = merge_rects(rect1, rect2)
                                if not merged_rect:
                                    merged_rect = m
                                else:
                                    merged_rect = merge_rects(merged_rect, m)
                            except StopIteration:
                                # CASE 2: Odd number of rects which overlap (the last is merged with intermediate result
                                merged_rect = merge_rects(merged_rect, rect1)
                                postprocessed_layout["annotations"][annotation_id] = {
                                    "category": category,
                                    "category_id": CATEGORIES_MAP.get(category),
                                    "bbox": merged_rect,
                                    "area": calculate_area(merged_rect),
                                }
                            # CASE 3: even number of rects to be merged
                            postprocessed_layout["annotations"][annotation_id] = {
                                "category": category,
                                "category_id": CATEGORIES_MAP.get(category),
                                "bbox": merged_rect,
                                "area": calculate_area(merged_rect),
                            }
                    annotation_id += 1

            with open(f"{filename}_corrected.json", "w") as fp:
                json.dump(postprocessed_layout, fp)
            img = Image.new("RGB", (612, 792), color=(255, 255, 255))
            draw = ImageDraw.Draw(img, "RGBA")

            for annotation in postprocessed_layout["annotations"].values():
                x1, y1, x2, y2 = annotation.get("bbox")
                col = COLORS_MAP.get(annotation.get("category"))
                draw.rectangle(
                    (x1, y1, x2, y2), outline=col + (200,), fill=col + (64,), width=2,
                )
            # Add border around image
            img = ImageOps.expand(img, border=2)
            imgpath = f"{layout.parent}/{layout.stem}_corrected.png"
            img.save(imgpath)


clean_generated_layouts("01_28_2022_19_46_25")
