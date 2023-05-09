import base64
import os
import io
from typing import Union
import numpy as np
from PIL import Image


def load_image(image: Union[str, bytes], to_base64: bool=False) -> Union[Image.Image, str, None]:
    if isinstance(image, bytes):
        return Image.open(io.BytesIO(image))
    elif os.path.isfile(image):
        if to_base64:
            return image_to_base64(image)
        with Image.open(image) as im:
            return Image.fromarray(np.asarray(im))
    return None


def save_image(
    image: Union[bytes, Image.Image, str], filepath: str, override: bool = False
) -> bool:
    if os.path.isfile(filepath) and not override:
        return False
    try:
        if isinstance(image, str):
            base64_to_image(image).save(filepath)
        elif isinstance(image, Image.Image):
            # this is an Image
            image.save(filepath)
        else:
            with open(filepath, "wb") as f:
                f.write(image)
    except OSError:
        return False
    return True


def crop_image(image: Image.Image, boundary: tuple) -> Image.Image:
    """
    Crop an image based on boundary defined in boundary tuple.
    """
    return image.crop(boundary)


def image_to_base64(
    image: Union[bytes, str, Image.Image], image_format: str = "png"
) -> str:
    if isinstance(image, str):
        # this is a filepath
        if not os.path.isfile(image):
            return ""
        with open(image, "rb") as f:
            image = f.read()
    elif isinstance(image, Image.Image):
        # this is an image
        rawbytes = io.BytesIO()
        image.save(rawbytes, format=image_format)
        image = rawbytes.getvalue()
    return (
        "data:image/{};base64,".format(image_format) + base64.b64encode(image).decode()
    )


def base64_to_image(image: str) -> Image.Image:
    tmp = image.split(",")
    if len(tmp) > 1:
        base64parts = tmp[1]
    else:
        base64parts = image
    return Image.open(io.BytesIO(base64.b64decode(base64parts)))


from skimage import io as skimageio
from skimage import transform
from skimage import img_as_ubyte


def load_and_transform_image_for_torch(
    img_filepath: str,
    dimension: tuple = (),
    force_rgb: bool = True,
    transpose: bool = True,
    use_ubyte: bool = False,
) -> np.ndarray:
    img = skimageio.imread(img_filepath)
    if force_rgb:
        img = img[:, :, :3]
    if dimension:
        img = transform.resize(img, dimension)
    if transpose:
        # swap color axis because
        # numpy image: H x W x C
        # torch image: C x H x W
        img = img.transpose((2, 0, 1))
    if use_ubyte:
        img = img_as_ubyte(img)
    return np.array(img)
