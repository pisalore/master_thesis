import argparse


def main_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only-labels', required=True,
                        help="Indicates if you want to generate only labels, without parsing process.")
    parser.add_argument('--pdfs-path', default="data/pdfs/",
                        help="The path to pdfs. It must be related to an xml-path: a pdf must have a related xml.")
    parser.add_argument('--xml-path', default="data/xml/",
                        help="The path to xml. It must be related to an pdfs-path: a xml must have a related xml.")
    parser.add_argument('--annotations-path', default=None,
                        help="Choose if generate annotated jpeg images from pdfs passing the path where save images."
                             "Useful for debugging or generating a specific dataset")
    parser.add_argument('--load-instances', default="",
                        help="The path to pickle file which contains a doc instances dictionary previously populated."
                             "Useful for split multiple computations.")
    args = parser.parse_args()
    return args
