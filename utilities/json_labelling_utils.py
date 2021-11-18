def calculate_segmentation(bbox):
    return [[bbox[0], bbox[1], bbox[2], bbox[1], bbox[2], bbox[3], bbox[0], bbox[3]]]


def calculate_area(bbox):
    b = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    return b * h


def generate_coco_bbox(bbox):
    x = bbox[0]
    y = bbox[1]
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return [x, y, width, height]
