import json

import numpy as np
import seaborn as sns
import torch
from PIL import ImageOps, Image, ImageDraw
from colormap import rgb2hex
from torch.nn import functional as F

from converters.objects_categories import COLORS_MAP


def gen_colors(num_colors):
    """
    Generate uniformly distributed `num_colors` colors. This works only if num categories is 11
    :param num_colors:
    :return:
    """
    palette = sns.color_palette(None, num_colors)
    rgb_triples = [[int(x[0] * 255), int(x[1] * 255), int(x[2] * 255)] for x in palette]
    dups = {tuple(x) for x in rgb_triples if rgb_triples.count(x) > 1}
    for d in dups:
        rgb_triples.remove(list(d))
        rgb_triples.append([0, 0, 0])

    return rgb_triples


def trim_tokens(tokens, bos, eos, pad=None):
    bos_idx = np.where(tokens == bos)[0]
    tokens = tokens[bos_idx[0] + 1 :] if len(bos_idx) > 0 else tokens
    eos_idx = np.where(tokens == eos)[0]
    tokens = tokens[: eos_idx[0]] if len(eos_idx) > 0 else tokens
    # tokens = tokens[tokens != bos]
    # tokens = tokens[tokens != eos]
    if pad is not None:
        tokens = tokens[tokens != pad]
    return tokens


def top_k_logits(logits, k):
    v, ix = torch.topk(logits, k)
    out = logits.clone()
    out[out < v[:, [-1]]] = -float("Inf")
    return out


def map_categories_to_colors(dataset):
    """
    Maps the colors used in DeepLayout to the input categories.
    :param dataset: JSONLayout dataset containing the annotations
    :return: hex colors' dict to categories
    """
    categories = dataset.categories
    colors = {}
    for idx, k in enumerate(categories.keys()):
        r, g, b = dataset.colors[idx]
        color_hex = rgb2hex(r, g, b)
        colors[color_hex] = {
            "category": categories[k]["name"],
            "color_rgb": (r, g, b),
        }
    return colors


@torch.no_grad()
def sample(model, x, steps, temperature=1.0, sample=False, top_k=None):
    """
    take a conditioning sequence of indices in x (of shape (b,t)) and predict the next token in
    the sequence, feeding the predictions back into the model each time. Clearly the sampling
    has quadratic complexity unlike an RNN that is only linear, and has a finite context window
    of block_size, unlike an RNN that has an infinite context window.
    """
    block_size = (
        model.module.get_block_size()
        if hasattr(model, "module")
        else model.getcond_block_size()
    )
    model.eval()
    for k in range(steps):
        x_cond = (
            x if x.size(1) <= block_size else x[:, -block_size:]
        )  # crop context if needed
        logits, _ = model(x_cond)
        # pluck the logits at the final step and scale by temperature
        logits = logits[:, -1, :] / temperature
        # optionally crop probabilities to only the top k options
        if top_k is not None:
            logits = top_k_logits(logits, top_k)
        # apply softmax to convert to probabilities
        probs = F.softmax(logits, dim=-1)
        # sample from the distribution or take the most likely
        if sample:
            ix = torch.multinomial(probs, num_samples=1)
        else:
            _, ix = torch.topk(probs, k=1, dim=-1)
        # append to the sequence and continue
        x = torch.cat((x, ix), dim=1)

    return x


def save_json_file(filename, postprocessed_layout):
    with open(f"{filename}.json", "w") as fp:
        json.dump(postprocessed_layout, fp)


def save_annotations_image(postprocessed_layout, layout, prefix=""):
    img = Image.new("RGB", (612, 792), color=(255, 255, 255))
    draw = ImageDraw.Draw(img, "RGBA")

    for annotation in postprocessed_layout["annotations"].values():
        x1, y1, x2, y2 = annotation.get("bbox")
        col = COLORS_MAP.get(annotation.get("category"))
        draw.rectangle(
            (x1, y1, x2, y2), outline=col + (200,), fill=col + (64,), width=2,
        )
    # Add border around image
    img = ImageOps.expand(img, border=2)
    imgpath = f"{layout.parent}/{layout.stem}_corrected{prefix}.png"
    img.save(imgpath)
