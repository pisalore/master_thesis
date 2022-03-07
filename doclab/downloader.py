import io
import random
from pathlib import Path
from random import choice, randrange

import requests
from PIL import Image
from bs4 import BeautifulSoup
from typing import List

base_img_url = "https://web.cse.ohio-state.edu/~chen.8028/VisPubImages/"


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
    images = requests.get(f"{base_img_url}/{category}/{year}/")
    soup = BeautifulSoup(images.content, "html.parser")
    for img in soup.findAll("a"):
        if "png" in img.get("href"):
            file_list.append(img.get("href"))
    return file_list


def resize_image(img: Image, to_width: int, to_height: int):
    """
    Resize the downloaded image in order to preserve the original aspect ratio.
    :param img: A PIL image
    :param to_width: The desired width
    :param to_height: The desired height
    :return: The resized image
    """
    img_w, img_h = img.size
    aspect = img_w / float(img_h)
    ideal_aspect = to_width / float(to_height)

    if aspect > ideal_aspect:
        # Then crop the left and right edges:
        new_width = int(ideal_aspect * img_h)
        offset = (img_w - new_width) / 2
        resize = (offset, 0, img_w - offset, img_h)
    else:
        # ... crop the top and bottom:
        new_height = int(img_w / ideal_aspect)
        offset = (img_h - new_height) / 2
        resize = (0, offset, img_w, img_h - offset)

    return img.crop(resize).resize((to_width, to_height), Image.ANTIALIAS)


def get_image(width: int, height: int, category: str) -> str:
    """
    Fetch a figure object from VISImageNavigator and return it in bytes.
    :param category: The category of the requested image
    :param width: The width to which the image must be resized to.
    :param height: The height to which the image must be resized to.
    :return: The path of the temporary image file
    """
    temp = Path("temp")
    temp.mkdir(mode=0o777, parents=False, exist_ok=True)
    random_year = "2020" if category == "Tables" else random_visi_year()
    file_names = get_year_objects_list(random_year, category)
    img_name = choice(file_names)
    requested_image = requests.get(
        f"{base_img_url}/{category}/{random_year}/{img_name}"
    )
    pil_image = Image.open(io.BytesIO(requested_image.content))
    resized_image = resize_image(pil_image, width, height)
    imgpath = f"{temp}/{img_name}"
    resized_image.save(imgpath, format="PNG")
    return imgpath


def formula_url():
    """
    Define a random equation sheet url
    :return: An equation sheet url for formula retrieving.
    """
    formula_id = random.choice(range(10, 400))
    return f"https://www.equationsheet.com/eqninfo/Equation-{formula_id}.html"


def get_formula():
    """
    Get a formula, in Latex code, from https://www.equationsheet.com/
    :return: A string representing a LateX equation
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0",
    }
    requested_html_formula = requests.get(f"{formula_url()}", headers=headers)
    decoded_html = requested_html_formula.content.decode("utf-8")
    soup = BeautifulSoup(decoded_html, "html.parser")
    textarea = soup.find("textarea")
    if textarea and "begin" not in textarea.get_text():
        print(textarea.get_text())
        return textarea.get_text()
    return ""


def write_formulas():
    """
    Retrieve formulas from https://www.equationsheet.com/, avoiding complex ones (that is,
    the ones with complex latex strucutres)
    :return: Writes a txt with formulas
    """
    with open("formula.txt", "w") as f:
        for i in range(400):
            print(i)
            f.write(f"r'{get_formula()}',")
            f.write("\n")
