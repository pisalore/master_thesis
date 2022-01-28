import argparse


def main_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only-labels",
        required=True,
        help="Indicates if you want to generate only labels, without parsing process.",
    )
    parser.add_argument(
        "--pdfs-path",
        default="data/pdfs/",
        help="The path to pdfs. It must be related to an xml-path: a pdf must have a related xml.",
    )
    parser.add_argument(
        "--xml-path",
        default="data/xml/",
        help="The path to xml. It must be related to an pdfs-path: a xml must have a related xml.",
    )
    parser.add_argument(
        "--annotations-path", help="The path where png images from pdf are saved."
    )
    parser.add_argument(
        "--debug",
        default="False",
        help="Indicate if png images have to be annotated with annotations bounding boxes."
        "Useful for debugging",
    )
    parser.add_argument(
        "--load-instances",
        default="docs_instances.pickle",
        help="The path to pickle file which contains a doc instances dictionary previously populated."
        "Useful for split multiple computations.",
    )
    args = parser.parse_args()
    return args


def json_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dirs",
        help="Delimited list input containing path to directories where xml annotations"
        "to be used generating coco json annotations are saved.",
        type=lambda s: [int(item) for item in s.split(",")],
    )


def gan_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", required=True, help="The model obtained by DeepLayout training."
    )
    parser.add_argument(
        "--json-data-path", required=True, help="The path to dataset json annotations."
    )
    parser.add_argument(
        "--n-generated",
        required=True,
        type=int,
        help="The number of layouts (paper pages) to be generated",
    )
    parser.add_argument(
        "--debug-imgs",
        default="False",
        help="A boolean which indicates if debug images must be saved",
    )
    args = parser.parse_args()
    return args
