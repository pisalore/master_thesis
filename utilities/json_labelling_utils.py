def calculate_segmentation(bbox):
    """
    Return segmentation for an annotation from its bounding box. For COCO json annotation format.
    See https://cocodataset.org/#format-data
    :param bbox: The annotation bounding box (x1, y1, x2, y2)
    :return: A segmentation list, formed by couples of (x, y) points.
    """
    return [
        [round(bbox[0], 2), round(bbox[1], 2),
         round(bbox[2], 2), round(bbox[1], 2),
         round(bbox[2], 2), round(bbox[3], 2),
         round(bbox[0], 2), round(bbox[3], 2)]]


def calculate_area(bbox):
    """
    Calculate annotation area from annotation bounding box.
    See https://cocodataset.org/#format-data
    :param bbox: The annotation bounding box (x1, y1, x2, y2)
    :return: The annotation area
    """
    b = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    return round(b * h, 2)


def generate_coco_bbox(bbox):
    """
    Generate bounding box in COCO format (x, y, width, height) from a bounding box formed by the upper left and bottom
    right points (x1, y1, x2, y2).
    See https://cocodataset.org/#format-data
    :param bbox: The annotation bounding box (x1, y1, x2, y2)
    :return: The COCO bounding box (x, y, width, height)
    """
    x = bbox[0]
    y = bbox[1]
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return [round(x, 2), round(y, 2), round(width, 2), round(height, 2)]
