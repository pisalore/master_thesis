from generators.text_generators import generate_random_text
from utilities.parser_utils import save_doc_instances, load_doc_instances


def main():
    categories = ["title", "authors", "keywords", "subtitles", "text"]
    generated_instances = {}
    for category in categories:
        generated_instances[category] = generate_random_text("../docs_instances.pickle", category, 1000)
        save_doc_instances("generated_instances.pickle", generated_instances)

    print(
        f"Generated {len(generated_instances['title'])} titles,"
        f" {len(generated_instances['authors'])} authors,"
        f" {len(generated_instances['keywords'])} keywords,"
        f" {len(generated_instances['subtitles'])} subtitles, "
        f"{len(generated_instances['text'])} texts.")


if __name__ == "__main__":
    main()
