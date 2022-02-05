import json
from pathlib import Path

from converters.objects_categories import CATEGORIES_MAP
from lgt.utils import (
    do_rects_overlap,
    merge_rects,
    save_json_file,
    save_annotations_image,
)
from utilities.json_labelling_utils import calculate_area


def split_annotations_by_categories(annotations):
    # save annotations occurrences belonging to the same category
    categorized_data = {}
    for k, o in annotations.items():
        category = o.get("category")
        if not categorized_data.get(category):
            categorized_data[category] = {}
        categorized_data[category][k] = {"instance": o, "overlaps_with": []}
    return categorized_data


def list_merge_objects(categorized_data):
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
    return categorized_data


def unique_ids(category_ids, value):
    merged_set = set()
    remove_indices = set()
    for merge_list in category_ids:
        if value in merge_list:
            merged_set.update(set(merge_list))
            remove_indices.add(category_ids.index(merge_list))
    category_ids = [i for j, i in enumerate(category_ids) if j not in remove_indices]
    category_ids.append(list(merged_set))
    return category_ids


def create_merge_list(categorized_data):
    to_be_merged_ids = {}
    for _, category_objs in categorized_data.items():
        # take the category from the first category objects dictionary
        # and instantiate the merge list for that category
        category = list(category_objs.values())[0]["instance"]["category"]
        to_be_merged_ids[category] = []
        # for each instance of a category, check intersections with all the other instances' overlap lists
        for k1, o1 in category_objs.items():
            merge_list = [k1]
            for k2, o2 in category_objs.items():
                if k2 != k1 and k2 in o1.get("overlaps_with"):
                    merge_list = [*merge_list, *o2.get("overlaps_with"), k2]
            # create distinct overlap lists
            to_be_merged_ids[category].append(list(set(merge_list)))
        to_be_merged_ids[category] = [
            list(x) for x in set(tuple(x) for x in to_be_merged_ids[category])
        ]
    correct_merged_dict = {}
    for category, category_ids in to_be_merged_ids.items():
        seen = set()
        corrected_ids = category_ids.copy()
        correct_merged_dict[category] = []
        for ids_list in category_ids:
            for value in ids_list:
                if value not in seen:
                    seen.add(value)
                    corrected_ids = unique_ids(corrected_ids, value)
        correct_merged_dict[category] = corrected_ids
    return correct_merged_dict


def create_postprocessed_layoout(
    filename, layout_data, annotations, correct_merged_dict
):
    postprocessed_layout = {
        "filename": filename,
        "layout_id": layout_data["layout_id"],
        "annotations": {},
    }
    annotation_id = 0
    for category, values in correct_merged_dict.items():
        for keys in values:
            # CASE 1: Single rect which does not overlap with any other rect
            if len(keys) == 1:
                postprocessed_layout["annotations"][annotation_id] = annotations[
                    keys[0]
                ]
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
    return postprocessed_layout


def clean_generated_layouts(layouts_dir):
    """
    Clean the generated layouts sampled from LayoutTransformer model.
    A layout is intended to be a single document page.
    :param layouts_dir: The directory containing all generated layouts
    :return: The cleaned layouts
    """
    for idx, layout in enumerate(Path(layouts_dir).rglob("*.json")):
        with open(layout) as f:
            layout_data = json.load(f)
            annotations = layout_data.get("annotations")
            filename = layout_data["filename"]
            # save annotations occurrences belonging to the same category
            categorized_data = split_annotations_by_categories(annotations)
            # for each instance, save objects' id with which it does overlap
            merged_data = list_merge_objects(categorized_data)
            # create correct merge data, ensuring uniqueness
            correct_merged_dict = create_merge_list(merged_data)
            # create post_processed dict annotations with merged rect of same category
            postprocessed_layout = create_postprocessed_layoout(
                filename, layout_data, annotations, correct_merged_dict
            )
            # save postprocessed json file and debug image
            save_json_file(filename, postprocessed_layout)
            save_annotations_image(postprocessed_layout, layout)


clean_generated_layouts("01_28_2022_19_46_25")
