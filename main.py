import logging
from pathlib import Path

from file_parser.parser import parse_doc
from file_parser.utils import save_doc_instances


def main():
    logging.basicConfig(filename='docs_parsing_log.log', level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(name)s %(message)s', force=True)
    logging.debug("Process started.")
    parsed_docs = {}
    for pdf_path, xml_path in zip(Path('data/pdfs/').rglob('*.pdf'), Path('data/xml/').rglob('*.xml')):
        pdf_id = pdf_path.stem
        try:
            parsed_docs[pdf_id] = parse_doc(pdf_path, xml_path)
            save_doc_instances(parsed_docs)
        except Exception as err:
            print("Error processing {}: TimeOut.".format(pdf_path))
            logging.error(err)

    logging.debug("Process terminated.")


if __name__ == "__main__":
    main()
