from pathlib import Path

from generators.text_generators import generate_random_text
from utilities.parser_utils import save_doc_instances, load_doc_instances

from args import text_generator_args


def main():
    args = text_generator_args()
    doc_instances = args.docs_instances
    papers_instances = load_doc_instances(doc_instances)
    categories = [cat for cat in args.categories.split(",")]
    authors_org = [cat for cat in args.orgs.split(",")]
    pickle_file_to_load = (
        args.load_instances if Path(args.load_instances).is_file() else None
    )
    generated_instances = (
        load_doc_instances(pickle_file_to_load) if pickle_file_to_load else {}
    )
    pickle_filename = args.pickle_filename
    for category in categories + authors_org:
        if category in authors_org:
            # if I am dealing with organizations or emails, I divide category key in authors.<category>
            category = f"authors.{category}"
        generated_instances[category] = generate_random_text(
            papers_instances, category, 1000
        )
        save_doc_instances(pickle_filename, generated_instances)
    # retrieve the emails
    generated_instances["emails"] = []
    for key, item in papers_instances.items():
        generated_instances["emails"] += item["authors"]["emails"]
    save_doc_instances(pickle_filename, generated_instances)

    print(
        f"Generated "
        f"{len(generated_instances['title'])} titles,"
        f" {len(generated_instances['authors'])} authors,"
        f" {len(generated_instances['authors.laboratories'])} laboratories,"
        f" {len(generated_instances['authors.departments'])} departments,"
        f" {len(generated_instances['authors.institutions'])} institutions,"
        f" {len(generated_instances['keywords'])} keywords,"
        f" {len(generated_instances['abstract'])} abstracts,"
        f" {len(generated_instances['subtitle'])} subtitles, "
        f"{len(generated_instances['text'])} texts."
    )


if __name__ == "__main__":
    main()
