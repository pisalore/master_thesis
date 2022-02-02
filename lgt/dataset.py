import numpy as np
import torch
from colormap import rgb2hex
from torch.utils.data.dataset import Dataset
from PIL import Image, ImageDraw, ImageOps
import json

from converters.objects_categories import CATEGORIES_MAP
from lgt.utils import gen_colors, trim_tokens
from utilities.json_labelling_utils import calculate_area


class Padding(object):
    def __init__(self, max_length, vocab_size):
        self.max_length = max_length
        self.bos_token = vocab_size - 3
        self.eos_token = vocab_size - 2
        self.pad_token = vocab_size - 1

    def __call__(self, layout):
        # grab a chunk of (max_length + 1) from the layout

        chunk = torch.zeros(self.max_length + 1, dtype=torch.long) + self.pad_token
        # Assume len(item) will always be <= self.max_length:
        chunk[0] = self.bos_token
        chunk[1 : len(layout) + 1] = layout
        chunk[len(layout) + 1] = self.eos_token

        x = chunk[:-1]
        y = chunk[1:]
        return {"x": x, "y": y}


class JSONLayout(Dataset):
    def __init__(self, json_path, max_length=None, precision=8):
        with open(json_path, "r") as f:
            data = json.loads(f.read())

        images, annotations, categories = (
            data["images"],
            data["annotations"],
            data["categories"],
        )
        self.size = pow(2, precision)

        self.categories = {c["id"]: c for c in categories}
        self.colors = gen_colors(len(self.categories))
        self.colors_categories_map = None

        self.json_category_id_to_contiguous_id = {
            v: i + self.size
            for i, v in enumerate([c["id"] for c in self.categories.values()])
        }

        self.contiguous_category_id_to_json_id = {
            v: k for k, v in self.json_category_id_to_contiguous_id.items()
        }

        self.vocab_size = self.size + len(self.categories) + 3  # bos, eos, pad tokens
        self.bos_token = self.vocab_size - 3
        self.eos_token = self.vocab_size - 2
        self.pad_token = self.vocab_size - 1

        image_to_annotations = {}
        for annotation in annotations:
            image_id = annotation["image_id"]

            if not (image_id in image_to_annotations):
                image_to_annotations[image_id] = []

            image_to_annotations[image_id].append(annotation)

        self.data = []
        for image in images:
            image_id = image["id"]
            height, width = float(image["height"]), float(image["width"])

            if image_id not in image_to_annotations:
                continue

            ann_box = []
            ann_cat = []
            for ann in image_to_annotations[image_id]:
                x, y, w, h = ann["bbox"]
                ann_box.append([x, y, w, h])
                ann_cat.append(
                    self.json_category_id_to_contiguous_id[ann["category_id"]]
                )

            # Sort boxes
            ann_box = np.array(ann_box)
            ind = np.lexsort((ann_box[:, 0], ann_box[:, 1]))
            ann_box = ann_box[ind]

            # Discretize boxes
            ann_box = self.quantize_box(ann_box, width, height)

            # Append the categories
            ann_cat = np.array(ann_cat)
            layout = np.concatenate([ann_cat.reshape(-1, 1), ann_box], axis=1)

            # Flatten and add to the dataset
            self.data.append(layout.reshape(-1))

        self.max_length = max_length
        if self.max_length is None:
            # for x in self.data:
            #     print(len(x))
            self.max_length = max([len(x) for x in self.data]) + 2  # bos, eos tokens
        self.transform = Padding(self.max_length, self.vocab_size)

    def quantize_box(self, boxes, width, height):

        # range of xy is [0, large_side-1]
        # range of wh is [1, large_side]
        # bring xywh to [0, 1]
        boxes[:, [2, 3]] = boxes[:, [2, 3]] - 1
        boxes[:, [0, 2]] = boxes[:, [0, 2]] / (width - 1)
        boxes[:, [1, 3]] = boxes[:, [1, 3]] / (height - 1)
        boxes = np.clip(boxes, 0, 1)

        # next take xywh to [0, size-1]
        boxes = (boxes * (self.size - 1)).round()

        return boxes.astype(np.int32)

    def reshape_layout(self, layout):
        layout = layout.reshape(-1)
        layout = trim_tokens(layout, self.bos_token, self.eos_token, self.pad_token)
        layout = layout[: len(layout) // 5 * 5].reshape(-1, 5)
        box = layout[:, 1:].astype(np.float32)
        box[:, [0, 1]] = box[:, [0, 1]] / (self.size - 1) * 255
        box[:, [2, 3]] = box[:, [2, 3]] / self.size * 256
        box[:, [2, 3]] = box[:, [0, 1]] + box[:, [2, 3]]
        return layout, box

    def get_layout_coords(self, layout, box):
        # Adjust boxes to be scaled for a paper page
        x1, y1, x2, y2 = box
        x1, y1, x2, y2 = x1 * 2.4, y1 * 3.1, x2 * 2.4, y2 * 3.1
        cat = layout[0]
        col = (
            self.colors[cat - self.size]
            if 0 <= cat - self.size < len(self.colors)
            else [0, 0, 0]
        )
        return x1, y1, x2, y2, cat, col

    def render(self, layout):
        # (612, 792) is the dimension of a paper page]
        img = Image.new("RGB", (612, 792), color=(255, 255, 255))
        draw = ImageDraw.Draw(img, "RGBA")
        layout, box = self.reshape_layout(layout)

        for i in range(len(layout)):
            x1, y1, x2, y2, cat, col = self.get_layout_coords(layout[i], box[i])
            draw.rectangle(
                (x1, y1, x2, y2),
                outline=tuple(col) + (200,),
                fill=tuple(col) + (64,),
                width=2,
            )
        # Add border around image
        img = ImageOps.expand(img, border=2)
        return img

    def save_annotations(self, layout, filename, it):
        json_annotated_layout = {
            "filename": filename,
            "layout_id": it,
            "annotations": {},
        }
        layout, box = self.reshape_layout(layout)
        for i in range(len(layout)):
            x1, y1, x2, y2, cat, col = self.get_layout_coords(layout[i], box[i])
            category = self.colors_categories_map[rgb2hex(*col)]["category"]
            bbox = [x1, y1, x2, y2]
            json_annotated_layout["annotations"][i] = {
                "category": category,
                "category_id": CATEGORIES_MAP.get(category),
                "bbox": bbox,
                "area": calculate_area(bbox),
            }
        with open(filename, "w") as fp:
            json.dump(json_annotated_layout, fp)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # grab a chunk of (block_size + 1) tokens from the data
        layout = torch.tensor(self.data[idx], dtype=torch.long)
        layout = self.transform(layout)
        return layout["x"], layout["y"]
