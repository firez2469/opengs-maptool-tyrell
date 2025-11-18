from PIL import Image


def load_grayscale_image(path: str) -> Image.Image:
    """
    Load image from disk, convert to grayscale (L).
    Assumes white background / black borders.
    """
    img = Image.open(path).convert("L")
    return img
