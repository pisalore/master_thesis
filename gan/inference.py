import datetime
from pathlib import Path, PurePosixPath

import torch
from torch.utils.data import DataLoader

from dataset import JSONLayout
from gan.model import GPTConfig, GPT
from gan.utils import sample, map_categories_to_colors
from args import gan_args


def inference(model_state_path, data_json_path, n_gen_layouts, debug):
    """
    Generate layouts from the learned DeepLayout model.
    :param debug: A boolean which indicates if debug images must be generated along with annotations.
    :param n_gen_layouts: The number of layouts we want to be generated.
    :param model_state_path: The path to the .pth file which contains the learned weights.
    :param data_json_path: The json containing the annotations.
    """
    dataset = JSONLayout(data_json_path)
    colors_categories = map_categories_to_colors(dataset)
    dataset.colors_categories_map = colors_categories
    model_conf = GPTConfig(
        dataset.vocab_size, dataset.max_length, n_layer=6, n_head=8, n_embd=512
    )
    generative_model = GPT(model_conf)
    generative_model.load_state_dict(torch.load(model_state_path))
    device = torch.cuda.current_device() if torch.cuda.is_available() else "cpu"
    generative_model = torch.nn.DataParallel(generative_model).to(device)
    loader = DataLoader(
        dataset,
        shuffle=True,
        pin_memory=True,
        batch_size=len(dataset.data),
        num_workers=0,
    )
    exp_dir = Path(datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S"))
    exp_dir.mkdir(mode=0o777, parents=False, exist_ok=True)
    for it in range(n_gen_layouts):
        for _, (x, y) in enumerate(loader):
            x_cond = x[:1].to(device)
            layouts = (
                sample(
                    generative_model,
                    x_cond[:, :6],
                    steps=dataset.max_length,
                    temperature=1.0,
                    sample=False,
                    top_k=None,
                )
                .detach()
                .cpu()
                .numpy()
            )

            for layout in layouts:
                layout_dir = Path(exp_dir.joinpath(f"layout_{it}"))
                layout_dir.mkdir(mode=0o777, parents=False, exist_ok=True)
                filename = f"{PurePosixPath(layout_dir).__str__()}/{it}"
                dataset.save_annotations(layout, f"{filename}.json", it)
                if debug:
                    img = dataset.render(layout)
                    img.save(f"{filename}.png")


args = gan_args()
pth = args.model
json_data = args.json_data_path
n_generated = args.n_generated
debug = args.debug_imgs.lower() in ("true", "t", "yes", "y", "1")
inference(pth, json_data, n_generated, debug)
