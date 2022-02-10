from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar

path = r'../data/pdfs/ICDAR19a/1aiwZSG8ppA0pUbRBHZZA7/5KGUvlXI6pKGkLqBu3YZ5.pdf'

extract_data = []

for page_layout in extract_pages(path):
    for element in page_layout:
        if isinstance(element, LTTextContainer):
            for text_line in element:
                for character in text_line:
                    if isinstance(character, LTChar):
                        font_size = character.size
            extract_data.append([font_size, (element.get_text()[:10]), element._objs[0]._objs[0].fontname])

for info in extract_data:
    print(info)