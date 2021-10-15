from pathlib import Path

import cv2


def create_point(coords):
    coords = tuple(int(num) for num in coords)
    return (coords[0], coords[1]), (coords[2], coords[3])


def annotate_imgs(png_path, doc_instances, thickness):
    # page
    idx_page = 1
    for png in Path(png_path).rglob('*.png'):
        img = cv2.imread(str(png))
        # Draw elements which relies only on first pages
        if idx_page == 1:
            # Title
            l_point, r_point = create_point(doc_instances["title"].get("coords"))
            cv2.rectangle(img, l_point, r_point, (255, 0, 0), thickness=thickness)
            # Authors
            l_point, r_point = create_point(doc_instances["authors"].get("coords"))
            cv2.rectangle(img, l_point, r_point, (0, 255, 0), thickness=thickness)
            # Keywords
            l_point, r_point = create_point(doc_instances["keywords"].get("coords"))
            cv2.rectangle(img, l_point, r_point, (0, 0, 255), thickness=thickness)
            # Abstract
            l_point, r_point = create_point(doc_instances["abstract"].get("coords"))
            cv2.rectangle(img, l_point, r_point, (255, 255, 0), thickness=thickness)
        if doc_instances["figures"].get(idx_page):
            for image in doc_instances["figures"].get(idx_page):
                l_point, r_point = create_point(image.get("coords"))
                cv2.rectangle(img, l_point, r_point, (0, 255, 255), thickness=thickness)
        if doc_instances["tables"].get(idx_page):
            for table in doc_instances["tables"].get(idx_page):
                l_point, r_point = create_point(table.get("coords"))
                cv2.rectangle(img, l_point, r_point, (255, 0, 255), thickness=thickness)
        if doc_instances["formulas"].get(idx_page):
            for formula in doc_instances["formulas"].get(idx_page):
                l_point, r_point = create_point(formula.get("coords"))
                cv2.rectangle(img, l_point, r_point, (0, 0, 0), thickness=thickness)
        cv2.imwrite(str(png), img)
        idx_page += 1
