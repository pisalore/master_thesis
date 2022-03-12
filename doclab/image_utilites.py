from pathlib import Path
import cv2


def resize_generated_images():
    """
    Utility method for resizing images to 612x792. This operation must be done since FPDF outputs 596x8412 PDF
    (A4 format) while we need 612x792 images (Letter format). To this aim, we crop 25 px rows from up and bottom, and
    we add 8 px columns to the right and to the left of images
    """
    for png_id, png_path in enumerate(Path("generated_pdfs_png").rglob("*.png")):
        img = cv2.imread(str(png_path))
        if img.shape[0:2] != (792, 612):
            crop_img = img[25:817, 0:596]
            crop_img = cv2.copyMakeBorder(
                crop_img,
                top=0,
                bottom=0,
                left=8,
                right=8,
                borderType=cv2.BORDER_CONSTANT,
                value=[255]*3
            )
            cv2.imwrite(str(png_path), crop_img)
            print(f"Cropped {png_id}")
        else:
            print(f"correct size {img.shape}")


def check_generated_images_size():
    """
    Utility method for checking images size. The correct size is 612x792
    """
    correct_size_images = []
    for png_id, png_path in enumerate(Path("C:/Users/loren/OneDrive/Desktop/generated_pdfs_png").rglob("*.png")):
        img = cv2.imread(str(png_path))
        if img.shape[0:2] == (792, 612):
            correct_size_images.append(int(png_path.stem.replace("_0", "")))
    print(correct_size_images)

