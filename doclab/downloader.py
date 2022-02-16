import io
from pathlib import Path
from tempfile import TemporaryFile
from random import choice, randrange

import requests
from PIL import Image
from bs4 import BeautifulSoup
from typing import List

base_url = "https://web.cse.ohio-state.edu/~chen.8028/VisPubImages/"


def random_visi_year() -> str:
    """
    Generate a random year between 1990 and 2020 (included)
    :return: A stirng representing a year in [2010, 2020]
    """
    return str(randrange(2010, 2021))


def get_year_objects_list(year: str, category: str) -> List[str]:
    """
    Return a list of string of images names for a given year.
    :param category: A string representing what is the type of the object we are looking for (Images, Equations, Tables)
    :param year: A string representing a year
    :return: A list of images names from VISImageNavigator
    """
    file_list = []
    images = requests.get(f"{base_url}/{category}/{year}/")
    soup = BeautifulSoup(images.content, "html.parser")
    for img in soup.findAll("a"):
        if "png" in img.get("href"):
            file_list.append(img.get("href"))
    return file_list


def get_image(width: int, height: int, category: str) -> str:
    """
    :param category: The category of the requested image
    :param width: The width to which the image must be resized to.
    :param height: The height to which the image must be resized to.
    Fetch a figure object from VISImageNavigator and return it in bytes.
    :return: The path of the temporary image file
    """
    temp = Path("temp")
    temp.mkdir(mode=0o777, parents=False, exist_ok=True)
    random_year = random_visi_year()
    file_names = get_year_objects_list(random_year, category)
    img_name = choice(file_names)
    requested_images = requests.get(f"{base_url}/{category}/{random_year}/{img_name}")
    pil_image = Image.open(io.BytesIO(requested_images.content))
    resized_image = pil_image.resize((width, height))
    imgpath = f"{temp}/{img_name}"
    resized_image.save(imgpath, format="PNG")
    return imgpath
