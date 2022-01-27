import torch
from torch.utils.data import DataLoader

from dataset import JSONLayout
from gan.model import GPTConfig, GPT
from gan.utils import sample, map_categories_to_colors


def inference(model_path, data_file_path):
    data = JSONLayout(data_file_path)
    data.colors_categories_map = map_categories_to_colors(data)
    model_conf = GPTConfig(
        data.vocab_size,
        data.max_length,
        n_layer=6,
        n_head=8,
        n_embd=512
    )
    generative_model = GPT(model_conf)
    generative_model.load_state_dict(torch.load(model_path))
    device = torch.cuda.current_device() if torch.cuda.is_available() else "cpu"
    generative_model = torch.nn.DataParallel(generative_model).to(device)
    loader = DataLoader(data, shuffle=True, pin_memory=True,
                        batch_size=64,
                        num_workers=0
                        )
    for it, (x, y) in enumerate(loader):
        x_cond = x[:30].to(device)
        layouts = sample(generative_model, x_cond[:, :6], steps=data.max_length, temperature=1.0, sample=False,
                         top_k=None).detach().cpu().numpy()


inference("checkpoint.pth", "../train.json")
