from pathlib import Path

from args import main_args
from file_parser.parser import parse_doc
from utilities.parser_utils import (
    save_doc_instances,
    load_doc_instances,
    count_pdf_pages,
)


def main():
    """
    The main process. Iterate over pdfs and xmls file in order to parse document structure and layout.
    For each document save a dictionary in docs_instances.pickle, thus it will be possible to access them after.
    Create a log file for debugging.
    only_labels is an argument which indicates if the main process will include also the file parsing. It is useful if
    data have been already process, and we want to generate json labels to be fed to a GAN model later.
    """
    args = main_args()
    annotations_path = args.annotations_path
    debug = args.debug.lower() in ("true", "t", "yes", "y", "1")
    pdfs_path, xml_path = args.pdfs_path, args.xml_path
    pickle_file_to_load = (
        args.load_instances if Path(args.load_instances).is_file() else None
    )
    pickle_filename = args.pickle_filename
    parsed_docs = (
        load_doc_instances(pickle_file_to_load) if pickle_file_to_load else {}
    )
    for pdf_path, xml_path in zip(
        Path(pdfs_path).rglob("*.pdf"), Path(xml_path).rglob("*.xml")
    ):
        print(f"Parsing {pdf_path}")
        pdf_id = pdf_path.stem
        try:
            num_pages = count_pdf_pages(pdf_path)
            # Ignore PDF which have less than three pages since maybe they are not scientific papers
            if num_pages > 3:
                parsed_docs[pdf_id] = parse_doc(
                    str(pdf_path), xml_path, annotations_path, debug
                )
                save_doc_instances(pickle_filename, parsed_docs)
        except TimeoutError as err:
            print(f"Error processing {pdf_path}: TimeOut.")


if __name__ == "__main__":
    main()
