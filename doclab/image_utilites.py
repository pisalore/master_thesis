from pathlib import Path
import cv2

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


