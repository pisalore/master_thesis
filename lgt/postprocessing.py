import json
from pathlib import Path

from args import post_processing_args

from lgt.postprocessing_utils import (
    split_annotations_by_categories,
    list_category_merge_objects,
    create_merge_list,
    merge_layout,
    list_overlap_different_objects,
    create_extra_rects,
    distance_overlapping_rects,
)
from lgt.utils import (
    save_json_file,
    save_annotations_image,
)


def main():
    """
    Clean the generated layouts sampled from LayoutTransformer model.
    A layout is intended to be a single document page.
    :param layouts_dir: The directory containing all generated layouts
    :return: The cleaned layouts
    """
    args = post_processing_args()
    layouts_dir = args.layouts_dir
    for layout in Path(layouts_dir).rglob("1.json"):
        with open(layout) as f:
            layout_data = json.load(f)
            annotations = layout_data.get("annotations")
            filename = layout_data["filename"]
            # save annotations occurrences belonging to the same category
            categorized_data = split_annotations_by_categories(annotations)
            # for each instance, save objects' id with which it does overlap
            merged_data = list_category_merge_objects(categorized_data)
            # create correct merge data, ensuring uniqueness
            correct_merged_dict = create_merge_list(merged_data)
            # create post_processed dict annotations with merged rect of same category
            postprocessed_layout = merge_layout(
                filename, layout_data["layout_id"], annotations, correct_merged_dict
            )
            save_annotations_image(postprocessed_layout, layout, "1")
            # create extra rects if a rect embeds others
            annotations = list_overlap_different_objects(
                postprocessed_layout["annotations"]
            )
            create_extra_rects(annotations)
            save_annotations_image(postprocessed_layout, layout, "2")
            # remove last overlaps and save
            distance_overlapping_rects(list_overlap_different_objects(annotations))
            # save postprocessed json file and debug image
            save_annotations_image(postprocessed_layout, layout, "3")
            save_json_file(filename, postprocessed_layout)
            print(f"{filename} post-processing completed.")


if __name__ == "__main__":
    main()
