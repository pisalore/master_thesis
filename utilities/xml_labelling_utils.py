from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET


def generate_object_xml_annotation(xml_annotation, coords, label):
    """
    Create the object tag to be added to XML root annotation. an object corresponds to one doc instance
    :param xml_annotation: ElementTree root Element
    :param coords: object annotation coordinates
    :param label: annotation label
    """
    # Create object tag and add the label (name)
    xml_object = ET.SubElement(xml_annotation, "object")
    ET.SubElement(xml_object, "name").text = label
    # Create bndbx annotation inside the object tag
    bndbox = ET.SubElement(xml_object, "bndbox")
    xmin, ymin, xmax, ymax = tuple(str(num) for num in coords)
    ET.SubElement(bndbox, "xmin").text = xmin
    ET.SubElement(bndbox, "xmax").text = xmax
    ET.SubElement(bndbox, "ymin").text = ymin
    ET.SubElement(bndbox, "ymax").text = ymax


def generate_pascal_voc_xml_labels(png_path, doc_instances):
    """
    Given each single image, create XML annotation file in Pascal VOC format to be used in labelImg
    :param png_path: path to image to be annotated in XML
    :param doc_instances: doc annotations instances obtained from parsing process
    """
    idx_page = 1
    for png in sorted(Path(png_path).rglob("*.png")):
        # Check if the XML annotation file exists, if not, create it
        xml_annotation_file = PurePosixPath(png).with_suffix(".xml")
        if not Path(xml_annotation_file).exists():
            # First, prepare the XML header
            # xml_annotation is the root of an XML file usable with labelImg
            xml_annotation = ET.Element("annotation")
            ET.SubElement(xml_annotation, "folder").text = str(png.parent.parts[-1])
            ET.SubElement(xml_annotation, "filename").text = str(png.name)
            ET.SubElement(xml_annotation, "path").text = str(png.absolute())
            xml_size = ET.SubElement(xml_annotation, "size")
            # Populate size tag; page size is fixed in our case
            ET.SubElement(xml_size, "width").text = "612"
            ET.SubElement(xml_size, "height").text = "792"
            if idx_page == 1:
                # Title
                if doc_instances["title"].get("coords"):
                    generate_object_xml_annotation(
                        xml_annotation, doc_instances["title"].get("coords"), "title"
                    )
                # Authors
                if doc_instances["authors"].get("coords"):
                    generate_object_xml_annotation(
                        xml_annotation,
                        doc_instances["authors"].get("coords"),
                        "authors",
                    )
                # Keywords
                if doc_instances["keywords"].get("coords"):
                    generate_object_xml_annotation(
                        xml_annotation,
                        doc_instances["keywords"].get("coords"),
                        "keywords",
                    )
                # Abstract
                if doc_instances["abstract"].get("coords"):
                    generate_object_xml_annotation(
                        xml_annotation,
                        doc_instances["abstract"].get("coords"),
                        "abstract",
                    )
            if doc_instances["figures"].get(idx_page):
                for image in doc_instances["figures"].get(idx_page):
                    generate_object_xml_annotation(
                        xml_annotation, image.get("coords"), "figure"
                    )
            if doc_instances["tables"].get(idx_page):
                for table in doc_instances["tables"].get(idx_page):
                    generate_object_xml_annotation(
                        xml_annotation, table.get("coords"), "table"
                    )
            if doc_instances["formulas"].get(idx_page):
                for formula in doc_instances["formulas"].get(idx_page):
                    generate_object_xml_annotation(
                        xml_annotation, formula.get("coords"), "formula"
                    )
            if doc_instances["subtitles"].get(idx_page):
                for subtitle in doc_instances["subtitles"].get(idx_page):
                    generate_object_xml_annotation(
                        xml_annotation, subtitle.get("coords"), "subtitle"
                    )
            if doc_instances["text"].get(idx_page):
                for text in doc_instances["text"].get(idx_page):
                    generate_object_xml_annotation(
                        xml_annotation, text.get("coords"), "text"
                    )
            # Generate xml string blob to be written
            b_xml = ET.tostring(xml_annotation)
            with open(xml_annotation_file, "wb") as f:
                f.write(b_xml)
        idx_page += 1
