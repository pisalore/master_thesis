from pathlib import Path
import xml.etree.ElementTree as ET

from utilities.xml_labelling_utils import generate_object_xml_annotation

PAGE_COORDS = (290, 740, 320, 750)
COPYRIGHT_COORDS = (50, 740, 170, 760)


def annotate_pages_and_copyright(png_dir):
    """
    Script to be used in xml annotations post-processing.
    Annotate pages number and copyright in xml files, automatically.
    :param png_dir: Dir to where detect xml files
    """
    for xml in Path(png_dir).rglob("*.xml"):
        tree = ET.parse(xml)
        root = tree.getroot()
        page_number = int(xml.stem.split("_")[-1])
        generate_object_xml_annotation(root, PAGE_COORDS, "text")
        if page_number == 0:
            generate_object_xml_annotation(root, COPYRIGHT_COORDS, "text")
        b_xml = ET.tostring(root)
        with open(xml, "wb") as f:
            f.write(b_xml)
        print(f"Processed {xml}.")
