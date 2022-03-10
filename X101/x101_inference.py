import os
from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from detectron2.data import build_detection_test_loader
from detectron2.config import get_cfg
from detectron2.data.datasets import register_coco_instances
from detectron2.engine import DefaultPredictor


def evaluate():
    # register validation dataset
    register_coco_instances(
        "val",
        {},
        f"/home/lpisaneschi/master_thesis/X101/coco/val.json",
        "/home/lpisaneschi/master_thesis/data/png/fully_annotated")

    cfg = get_cfg()
    cfg.merge_from_file("/home/lpisaneschi/master_thesis/X101/configs/X101.yaml")
    cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR, "model_final.pth")
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.8

    #Use the final weights generated after successful training for inference  
    cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR, "model_final.pth")
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.8  # set the testing threshold for this model
    #Pass the validation dataset
    cfg.DATASETS.TEST = ("val", )
    predictor = DefaultPredictor(cfg)
    evaluator = COCOEvaluator("val", cfg, False, output_dir="/home/lpisaneschi/master_thesis/X101/predictions/predictions_no_augmentation/")
    
    val_loader = build_detection_test_loader(cfg, "val")

    #Use the created predicted model in the previous step
    inference_on_dataset(predictor.model, val_loader, evaluator)

evaluate()