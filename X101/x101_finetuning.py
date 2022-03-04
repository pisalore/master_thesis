import random
import cv2
from detectron2.checkpoint import DetectionCheckpointer
from detectron2.modeling import build_model
from detectron2.config import get_cfg
from detectron2.data import MetadataCatalog, DatasetCatalog
from detectron2.utils.visualizer import Visualizer
from detectron2.data.datasets import register_coco_instances


from converters.objects_categories import CATEGORIES_MAP

# only for debug purposes
# state_dict = torch.load("/home/lpisaneschi/master_thesis/X101/model.pth")


cfg = get_cfg()
cfg.merge_from_file("/home/lpisaneschi/master_thesis/X101/configs/X101.yaml")
model = build_model(cfg)

DetectionCheckpointer(model).load(
    "/home/lpisaneschi/master_thesis/X101/model.pth")

for d in ["train", "val"]:
    register_coco_instances(
        d,
        {},
        f"/home/lpisaneschi/master_thesis/X101/coco/{d}.json",
        "/home/lpisaneschi/master_thesis/data/png/fully_annotated")

train_dict = DatasetCatalog.get("train")
metadata = MetadataCatalog.get("train")
for i, d in enumerate(random.sample(train_dict, 3)):
    img = cv2.imread(d["file_name"])
    visualizer = Visualizer(img[:, :, ::-1], metadata=metadata)
    vis = visualizer.draw_dataset_dict(d)
    cv2.imwrite(f'Image{i}.png', vis.get_image()[:, :, ::-1])
