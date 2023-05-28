import os

from utilities.constants import BASE64IMAGE
from utilities.constants import KEY_WIDTH
from utilities.constants import KEY_HEIGHT
from utilities.constants import KEY_BASE_MODEL

from utilities.config import Config
from utilities.logger import DummyLogger
from utilities.images import image_to_base64
from utilities.images import load_image
from utilities.images import save_image
from utilities.images import base64_to_image


def gfpgan(
    gfpgan_folderpath, job_uuid, img_filepath, config=Config(), logger=DummyLogger()
):
    if not os.path.isdir(gfpgan_folderpath):
        logger.error(f"unable to find GFPGAN folder {gfpgan_folderpath}")
        return {}

    if not os.path.isfile(img_filepath):
        logger.error(f"unable to find image file {img_filepath}")
        return {}

    tmp_output_dir = f"/tmp/{job_uuid}"
    os.makedirs(tmp_output_dir, exist_ok=True)

    cmd = f"/usr/bin/python {gfpgan_folderpath}/inference_gfpgan.py -i {img_filepath} -o {tmp_output_dir} -v 1.3 -s {config.get_steps()} -w {config.get_strength()}"
    logger.info(f"running: {cmd}")
    os.system(cmd)

    img_output_path = os.path.join(tmp_output_dir, "restored_imgs", os.path.basename(img_filepath))
    logger.info(f"image path: {img_output_path}")
    try:

        image = load_image(img_output_path)
        width, height = image.size
        return {
            BASE64IMAGE: image_to_base64(image),
            KEY_WIDTH: width,
            KEY_HEIGHT: height,
            KEY_BASE_MODEL: "gfpgan",
        }
    except Exception as e:
        logger.error(f"Scaling failed: {e}")
    return {}
