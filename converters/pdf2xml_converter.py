import logging
import pathlib
import sys
from pathlib import Path

import requests

logging.basicConfig(filename='grobid-import.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)

# Create the xml directory, checking whatever it exists or not.
xml_path = pathlib.Path("../data/xml")
xml_path.mkdir(mode=0o777, parents=False, exist_ok=True)

# If preprocess-data, we want to restructure the directories tree in order to have a standard organization for further
# processing
if "preprocess-data" in sys.argv:
    for pdf_path in Path('../data/pdfs/').rglob('*.pdf'):
        dir_path = pathlib.Path(pdf_path.parent.joinpath(pdf_path.stem))
        dir_path.mkdir(mode=0o777, parents=False, exist_ok=True)
        logger.info("Preprocess file: ", dir_path / pdf_path.name)
        pdf_path.rename(dir_path / pdf_path.name)

# For each pdf file path, create the related xml path, call Grobid service via requests, and save the xml file
for pdf_path in Path('../data/pdfs').rglob('*.pdf'):
    try:
        xml_path = pathlib.Path("../data/xml")
        xml_path = xml_path.joinpath(pdf_path.relative_to("../data/pdfs").parents[0], pdf_path.stem + ".xml")
        xml_path.parents[0].mkdir(parents=True, exist_ok=True)
        print("Processing {}...".format(pdf_path))
        # Open PDF
        pdf = open(pdf_path, "rb")
        # Request Grobid xml
        xml_response_content = requests.post(url="http://localhost:8070/api/processFulltextDocument",
                                             files={"input": pdf.read()},
                                             data={"teiCoordinates": ["persName", "figure", "ref",
                                                                      "biblStruct", "formula", "s", "head"]})
        # Write XML file
        xml_file = open(xml_path, "a")
        xml_file.write(xml_response_content.text)
        xml_file.close()
        pdf_to_xml_txt = open("pdf2xml.txt", "a")
        pdf_to_xml_txt.write("{} {}\n".format(pdf_path.__str__(), xml_path.__str__()))
    except Exception as err:
        logger.error(err)
