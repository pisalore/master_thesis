from pathlib import Path

import cv2


def create_point(coords):
    """
    Create left upper and bottom right points starting from a tuple of floats, for opencv processing.
    :param coords: tuple of float numbers (x1, y1, x2, y2)
    :return: tuple of int numbers (x1, y1, x2, y2)
    """
    coords = tuple(int(num) for num in coords)
    return (coords[0], coords[1]), (coords[2], coords[3])


def annotate_imgs(png_path, doc_instances, thickness):
    """
    Annotate images created from a PDF.
    Annotate title, keywords, abstract and authors in first page; then, images, tables and formulas.
    :param png_path: path to directory containing the pages images
    :param doc_instances: dict containing coordinates to be used in pdf instances annotation process
    :param thickness: annotation thickness
    :return: Annotated PDF images
    """
    idx_page = 1
    for png in sorted(Path(png_path).rglob("*.png")):
        img = cv2.imread(str(png))
        # Draw elements which relies only on first pages
        if idx_page == 1:
            # Title
            if doc_instances["title"].get("coords"):
                l_point, r_point = create_point(doc_instances["title"].get("coords"))
                cv2.rectangle(img, l_point, r_point, (255, 0, 0), thickness=thickness)
            # Authors
            if doc_instances["authors"].get("coords"):
                l_point, r_point = create_point(doc_instances["authors"].get("coords"))
                cv2.rectangle(img, l_point, r_point, (0, 255, 0), thickness=thickness)
            # Keywords
            if doc_instances["keywords"].get("coords"):
                l_point, r_point = create_point(doc_instances["keywords"].get("coords"))
                cv2.rectangle(img, l_point, r_point, (0, 0, 255), thickness=thickness)
            # Abstract
            if doc_instances["abstract"].get("coords"):
                l_point, r_point = create_point(doc_instances["abstract"].get("coords"))
                cv2.rectangle(img, l_point, r_point, (255, 255, 0), thickness=thickness)
        if doc_instances["figures"].get(idx_page):
            for image in doc_instances["figures"].get(idx_page):
                l_point, r_point = create_point(image.get("coords"))
                cv2.rectangle(img, l_point, r_point, (0, 255, 255), thickness=thickness)
        if doc_instances["tables"].get(idx_page):
            for table in doc_instances["tables"].get(idx_page):
                l_point, r_point = create_point(table.get("coords"))
                cv2.rectangle(
                    img, l_point, r_point, (123, 238, 104), thickness=thickness
                )
        if doc_instances["formulas"].get(idx_page):
            for formula in doc_instances["formulas"].get(idx_page):
                l_point, r_point = create_point(formula.get("coords"))
                cv2.rectangle(img, l_point, r_point, (0, 0, 0), thickness=thickness)
        if doc_instances["subtitles"].get(idx_page):
            for subtitle in doc_instances["subtitles"].get(idx_page):
                l_point, r_point = create_point(subtitle.get("coords"))
                cv2.rectangle(img, l_point, r_point, (200, 0, 255), thickness=thickness)
        if doc_instances["text"].get(idx_page):
            for text in doc_instances["text"].get(idx_page):
                l_point, r_point = create_point(text.get("coords"))
                cv2.rectangle(
                    img, l_point, r_point, (200, 200, 255), thickness=thickness
                )
        cv2.imwrite(str(png), img)
        idx_page += 1
