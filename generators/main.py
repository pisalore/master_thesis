from generators.text_generators import generate_random_text
from utilities.parser_utils import save_doc_instances, load_doc_instances


def main():
    categories = ["title", "authors", "keywords", "subtitles", "text"]
    generated_instances = {}
    for category in categories:
        generated_instances[category] = generate_random_text("../docs_instances.pickle", category, 200)
        save_doc_instances("generated_instances.pickle", generated_instances)
    a = load_doc_instances("generated_instances.pickle")


if __name__ == "__main__":
    main()
