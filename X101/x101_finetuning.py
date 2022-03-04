from detectron2.checkpoint import DetectionCheckpointer
from detectron2.modeling import build_model
from detectron2.config import get_cfg
import torch

cfg = get_cfg()
cfg.merge_from_file("/home/lpisaneschi/master_thesis/X101/configs/X101.yaml")
model = build_model(cfg)
state_dict = torch.load("/home/lpisaneschi/master_thesis/X101/model.pth")

DetectionCheckpointer(model).load("/home/lpisaneschi/master_thesis/X101/model.pth")