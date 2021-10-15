import pathlib
from pdf2image import convert_from_path
from PyPDF2.pdf import PdfFileReader
import shutil


def convert_pdf_2_images(png_dir, pdf_path):
    # Create the png directory, checking whatever it exists or not, and a temporary directory for PIL images conversion.
    png_path = pathlib.Path(png_dir)
    png_path.mkdir(mode=0o777, parents=False, exist_ok=True)
    png_path = png_path.joinpath(pdf_path.relative_to("data/pdfs")).parents[0]
    png_path_tmp = png_path.joinpath(pathlib.Path("tmp"))
    png_path.mkdir(parents=True, exist_ok=True)
    png_path_tmp.mkdir(parents=True, exist_ok=True)

    print("Converting {} from pdf to PNG...".format(png_path.name))
    reader = PdfFileReader(open(pdf_path, mode="rb"))
    try:
        page_number = reader.getNumPages()
    except Exception:
        page_number = reader.getNumPages()  # PyPDF2 bug
    images_from_path = convert_from_path(pdf_path, dpi=72, output_folder=png_path_tmp, last_page=page_number, first_page=0)
    for idx, page in enumerate(images_from_path):
        base_filename = png_path.joinpath(pathlib.Path(pdf_path.stem + "_{}.png".format(idx)))
        if not base_filename.exists():
            page.save(pathlib.Path(base_filename), 'PNG')

    shutil.rmtree(png_path_tmp)
    print('PDF file successfully converted.')
    return png_path
