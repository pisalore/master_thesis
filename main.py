import logging
from pathlib import Path

from file_parser.parser import parse_doc
from file_parser.utils import save_doc_instances


def main():
    """
    The main process. Iterate over pdfs and xmls file in order to parse document structure and layout.
    For each document save a dictionary in docs_instances.pickle, thus it will be possible to access them after.
    Create a log file for debugging.
    """
    logging.basicConfig(filename='docs_parsing_log.log', level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(name)s %(message)s', force=True)
    logging.debug("Process started.")
    parsed_docs = {}
    for pdf_path, xml_path in zip(Path('data/pdfs/').rglob('34BXtZHF3Jfjmu3cgq1O6Q.pdf'), Path('data/xml/').rglob('34BXtZHF3Jfjmu3cgq1O6Q.xml')):
        pdf_id = pdf_path.stem
        try:
            parsed_docs[pdf_id] = parse_doc(str(pdf_path), xml_path)
            save_doc_instances(parsed_docs)
        except TimeoutError as err:
            print("Error processing {}: TimeOut.".format(pdf_path))
            logging.error(err)

    logging.debug("Process terminated.")


if __name__ == "__main__":
    main()
