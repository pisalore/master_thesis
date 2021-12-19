import logging
from pathlib import Path

from args import main_args
from converters.pickle2json_labels_converter import generate_json_labels
from file_parser.parser import parse_doc
from utilities.parser_utils import save_doc_instances, load_doc_instances, count_pdf_pages


def main():
    """
    The main process. Iterate over pdfs and xmls file in order to parse document structure and layout.
    For each document save a dictionary in docs_instances.pickle, thus it will be possible to access them after.
    Create a log file for debugging.
    only_labels is an argument which indicates if the main process will includes also the file parsing. It is useful if
    data have been already process, and we want to generate json labels to be fed to a GAN model later.
    """
    args = main_args()
    annotations_path = args.annotations_path
    pdfs_path, xml_path = args.pdfs_path, args.xml_path
    only_labels = args.only_labels.lower() in ("true", "t", "yes", "y", "1")
    pickle_file_to_load = args.load_instances if Path(args.load_instances).is_file() else None
    if not only_labels:
        logging.basicConfig(filename='docs_parsing_log.log', level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(name)s %(message)s', force=True)
        logging.debug("Process started.")
        parsed_docs = load_doc_instances(pickle_file_to_load) if pickle_file_to_load else {}
        for pdf_path, xml_path in zip(Path(pdfs_path).rglob('*.pdf'), Path(xml_path).rglob('*.xml')):
            print("Parsing {}".format(pdf_path))
            pdf_id = pdf_path.stem
            try:
                num_pages = count_pdf_pages(pdf_path)
                # Ignore PDF which have less than three pages since maybe they are not scientific papers
                if num_pages > 3:
                    parsed_docs[pdf_id] = parse_doc(str(pdf_path), xml_path, annotations_path)
                    save_doc_instances(parsed_docs)
            except TimeoutError as err:
                print("Error processing {}: TimeOut.".format(pdf_path))
                logging.error(err)

        logging.debug("Process terminated.")

    # Generate json labels like PubLayNet
    generate_json_labels(Path("docs_instances.pickle"), Path("data/png"))


if __name__ == "__main__":
    main()
