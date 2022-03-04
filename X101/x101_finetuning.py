import random
import cv2
from detectron2.checkpoint import DetectionCheckpointer
from detectron2.modeling import build_model
from detectron2.config import get_cfg
from detectron2.data import MetadataCatalog, DatasetCatalog
from detectron2.utils.visualizer import Visualizer
from detectron2.data.datasets import register_coco_instances
from detectron2.engine import DefaultTrainer


def finetune_x101(example_img=None):
    # only for debug purposes
    # state_dict = torch.load("/home/lpisaneschi/master_thesis/X101/model.pth")
    cfg = get_cfg()
    cfg.merge_from_file("/home/lpisaneschi/master_thesis/X101/configs/X101.yaml")

    # cfg.SOLVER.MAX_ITER = 10  #No. of iterations   
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 11
    cfg.OUTPUT_DIR = "/home/lpisaneschi/master_thesis/X101/finetuned_model"
    
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
    if example_img:
        for i, d in enumerate(random.sample(train_dict, example_img)):
            img = cv2.imread(d["file_name"])
            visualizer = Visualizer(img[:, :, ::-1], metadata=metadata)
            vis = visualizer.draw_dataset_dict(d)
            cv2.imwrite(f'Image{i}.png', vis.get_image()[:, :, ::-1])

    trainer = DefaultTrainer(cfg)
    trainer.resume_or_load(resume=False)
    trainer.train()

if __name__ == '__main__':
    finetune_x101()
