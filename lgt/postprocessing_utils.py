from collections import namedtuple

from converters.objects_categories import CATEGORIES_MAP
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


def split_annotations_by_categories(annotations):
    """
    Organize original annotations occurrences splitting them by category
    :param annotations: the annotations of a given layout generated by layoutTransformer
    :return: A dict of annotations where main keys annotation categories
    """
    categorized_data = {}
    for k, o in annotations.items():
        category = o.get("category")
        if not categorized_data.get(category):
            categorized_data[category] = {}
        categorized_data[category][k] = {"instance": o, "overlaps_with": []}
    return categorized_data


def list_category_merge_objects(categorized_data):
    """
    Add a new key to an annotation instance, i.e. "overlaps_with", and populate it with a list of instances id which
    overlap the referred instance itself.
    :param categorized_data: A dict of annotations divided by category
    :return: A dict of annotations divided by category where each instance has a list of overlapping instances ids
    """
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
    """
    Iterate over all merge lsit for a given category, ensuring that an id appears in only one list
    :param category_ids: A list of ids merge lists
    :param value: The value (instance id) to be checked
    :return: A list of ids merge list in which the value (an istance id) appears only once
    """
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
    """
    Create a categorized merge dict ensuring that an "overlap id" appears only once, for a better bounding boxes merge
    in post-processing.
    :param categorized_data:  A dict of annotations divided by category
    :return: A dict of annotations divided by category where each instance has a list of overlapping ids instances,
    where each id appears only once, considering overall overlap lists.
    """
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


def merge_layout(filename, layout_id, annotations, correct_merged_dict):
    """
    Does the effective merge post-processing operation, merging overlapping rects belonging to same category.
    :param filename: Original annotation json filename for the given layout
    :param layout_id: Original layout id
    :param annotations: The annotations to work with
    :param correct_merged_dict: A dict of id of instances to be merged, where ids appear only once
    :return: The layout with merged instances
    """
    postprocessed_layout = {
        "filename": filename,
        "layout_id": layout_id,
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
                        # CASE 2: Odd number of rects which overlap (the last is merged with intermediate result)
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


def list_overlap_different_objects(data):
    """
    Add an "overlaps_with" key to an annotation, where are listed all overlapping objects (with different categories)
    :param data: A dict of annotations where overlapping objects belonging to same category have been merged
    :return: A dict of annotations where for each annotation overlapping id instances are listed
    """
    for k1, o1 in data.items():
        overlaps = []
        for k2, o2 in data.items():
            if k2 != k1:
                if do_rects_overlap(o1.get("bbox"), o2.get("bbox")):
                    overlaps.append(k2)
        o1["overlaps_with"] = overlaps
    return data


def distance_overlapping_rects(data):
    """
    Distances annotations rects
    :param data: Layout annotations
    :return: The final post-processed layout
    """
    for k, selected_rect in data.items():
        for overlap_rect_key in selected_rect.get("overlaps_with"):
            overlap_rect = data.get(overlap_rect_key)

            overlaps_below = selected_rect.get("bbox")[1] < overlap_rect.get("bbox")[1]
            change_rect = (
                selected_rect
                if selected_rect.get("area") > overlap_rect.get("area")
                else overlap_rect
            )
            if overlaps_below:
                overlap_y = abs(
                    overlap_rect.get("bbox")[1] - selected_rect.get("bbox")[3]
                )
                if overlaps_below and change_rect == selected_rect:
                    change_rect.get("bbox")[3] = (
                        change_rect.get("bbox")[3] - overlap_y - 5
                    )
                else:
                    change_rect.get("bbox")[1] = (
                        change_rect.get("bbox")[1] + overlap_y + 5
                    )
            else:
                overlap_y = abs(
                    overlap_rect.get("bbox")[3] - selected_rect.get("bbox")[1]
                )
                if change_rect == selected_rect:
                    change_rect.get("bbox")[1] = (
                        change_rect.get("bbox")[1] + overlap_y + 5
                    )
                else:
                    change_rect.get("bbox")[3] = (
                        change_rect.get("bbox")[3] - overlap_y - 5
                    )
    return data


def create_extra_rects(annotations):
    """
    Create rects, if necessary, splitting  those who embeds others, of different categories
    :param annotations: A layout annotations
    :return: Layout annotations where embedding ones are split up
    """
    Rectangle = namedtuple("Rectangle", "xmin ymin xmax ymax")
    extra_rects = {}
    extra_rect_id = len(annotations.items())
    rects_to_be_removed = []

    for k1, v1 in annotations.items():
        rect1 = Rectangle(*v1.get("bbox"))
        xmin, xmax = rect1.xmin, rect1.xmax
        for k2, v2 in annotations.items():
            rect2 = Rectangle(*v2.get("bbox"))
            if k1 != k2:
                # check if one rect embeds the other
                embedding1 = rect1.ymin < rect2.ymin and rect1.ymax > rect2.ymax
                xrange1 = xmin - 10 <= rect2.xmin and rect2.xmax <= xmax + 10
                if embedding1 and xrange1:
                    # the rect to be split is the wider one
                    # and the new rect to be created must have the wider rect category
                    category = v1.get("category") if embedding1 else v2.get("category")
                    rects_to_be_removed.append(
                        k1
                    ) if embedding1 else rects_to_be_removed.append(k2)
                    bbox = [
                        min(rect1.xmin, rect2.xmin),
                        max(rect1.ymin, rect2.ymin) - 50,
                        min(rect1.xmax, rect2.xmax),
                        max(rect1.ymin, rect2.ymin) + 5,
                    ]
                    extra_rects[extra_rect_id] = {
                        "category": category,
                        "category_id": extra_rect_id,
                        "bbox": bbox,
                        "" "area": calculate_area(bbox),
                    }
                    extra_rect_id += 1
    for k in set(rects_to_be_removed):
        annotations.pop(k, None)
    annotations.update(extra_rects)
    return annotations
