from nltk import word_tokenize, TreebankWordDetokenizer
from nltk.lm import MLE
from nltk.lm.preprocessing import padded_everygram_pipeline
from random import randrange, randint
import numpy as np
import math

detokenize = TreebankWordDetokenizer().detokenize


def generate_sent(model, num_words, random_seed=42):
    """
    :param model: An ngram language model from `nltk.lm.model`.
    :param num_words: Max no. of words to generate.
    :param random_seed: Seed value for random.
    :return The de-tokenized generated string
    """
    content = []
    for token in model.generate(num_words=num_words, random_seed=random_seed):
        if token == "<s>":
            continue
        if token == "</s>":
            break
        content.append(token)
    return detokenize(content)


def generate_random_text(papers_instances, category, text_num):
    """
    Generate random text using NLTK n-grams from parsed pdf contents, saved during parsing process.
    :param papers_instances: The loaded parsed doc_instances
    :param category: the category for which we want to create text
    :param text_num: the number of text objects to be created
    :return generated_instances: A dictionary containing generated sentences of the given category
    """
    all_text, all_text_lengths, text = [], [], ""
    generated_instances = []
    for paper in papers_instances.keys():
        # Get category text and save it, along with text length in order to calculate the mean of words to use
        # for text generation
        if "." in category:
            authors, org_name = category.split(".")
            instance = papers_instances.get(paper).get(authors)
        else:
            instance = papers_instances.get(paper).get(category)
        if category == "title" and instance.get("content"):
            text = instance.get("content")
        elif category in ["keywords", "authors"] and instance.get("terms"):
            text = ", ".join(instance.get("terms"))
        elif category == "subtitles" and instance.get("titles_contents"):
            text = instance.get("titles_contents")
            if text:
                all_text += text
        elif category == "abstract" and instance.get("content"):
            text = f"Abstract - {instance.get('content')}"
        elif category == "text":
            for page in instance.keys():
                for content in instance[page]:
                    if content.get("content"):
                        text = content.get("content")
                        all_text.append(text)
        # if the "." is inside the category, I am dealing with authors affiliations
        elif "." in category:
            text = instance.get(org_name)
            if text:
                all_text += text
        if text and category not in ["text", "subtitles"] and "." not in category:
            all_text.append(text)
        # Text length distributions
        if category in ["keywords", "authors", "text", "title", "abstract"]:
            all_text_lengths.append(len(text.split(" ")))
        # Calculate mean length in subtitles lists
        elif category == "subtitles" and instance.get("titles_contents"):
            all_text_lengths.append(
                math.ceil(
                    np.mean(
                        [len(a.split(" ")) for a in instance.get("titles_contents")]
                    )
                )
            )
        elif "." in category and instance.get(org_name):
            all_text_lengths.append(
                math.ceil(np.mean([len(a.split(" ")) for a in instance.get(org_name)]))
            )

    # Tokenize the text.
    corpus = [word_tokenize(s) for s in all_text]
    # Preprocess the tokenized text for 3-grams language modelling
    n = 3
    train_data, padded_sents = padded_everygram_pipeline(n, corpus)
    model = MLE(n)
    model.fit(train_data, padded_sents)

    print(f"Generate {category} stuff...")
    for i in range(text_num):
        num_words = all_text_lengths[randrange(0, len(all_text_lengths))]
        sentence = generate_sent(model, num_words, random_seed=randint(1, 150))
        if sentence and not any(x in sentence for x in ["(cid:", "<s>", "</ s>"]):
            generated_instances.append(sentence)
    # Distinct elements
    return list(set(generated_instances))
