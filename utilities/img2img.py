import torch
from typing import Union
from PIL import Image

from utilities.constants import BASE64IMAGE
from utilities.constants import KEY_SEED
from utilities.constants import KEY_WIDTH
from utilities.constants import KEY_HEIGHT
from utilities.constants import KEY_STEPS
from utilities.config import Config
from utilities.logger import DummyLogger
from utilities.memory import empty_memory_cache
from utilities.model import Model
from utilities.times import get_epoch_now
from utilities.images import image_to_base64
from utilities.images import base64_to_image


class Img2Img:
    """
    Img2Img class.
    """

    def __init__(
        self,
        model: Model,
        output_folder: str = "",
        logger: DummyLogger = DummyLogger(),
    ):
        self.model = model
        self.__device = "cpu" if not self.model.use_gpu() else "cuda"
        self.__output_folder = output_folder
        self.__logger = logger

    def brunch(self, prompt: str, negative_prompt: str = ""):
        self.breakfast()
        self.lunch(prompt, negative_prompt)

    def breakfast(self):
        pass

    def lunch(
        self,
        prompt: str,
        negative_prompt: str = "",
        reference_image: Union[Image.Image, None, str] = None,
        config: Config = Config(),
    ) -> dict:
        if not prompt:
            self.__logger.error("no prompt provided, won't proceed")
            return {}
        if reference_image is None:
            return {}

        self.model.set_img2img_scheduler(config.get_scheduler())

        t = get_epoch_now()
        seed = config.get_seed()
        generator = torch.Generator(self.__device).manual_seed(seed)
        self.__logger.info("current seed: {}".format(seed))

        if isinstance(reference_image, str):
            reference_image = (
                base64_to_image(reference_image)
                .thumbnail(config.get_width(), config.get_height())
                .convert("RGB")
            )

        result = self.model.img2img_pipeline(
            prompt=prompt,
            image=reference_image,
            negative_prompt=negative_prompt,
            guidance_scale=config.get_guidance_scale(),
            strength=config.get_strength(),
            num_inference_steps=config.get_steps(),
            generator=generator,
            callback=None,
            callback_steps=10,
        )

        if self.__output_folder:
            out_filepath = "{}/{}.png".format(self.__output_folder, t)
            result.images[0].save(out_filepath)
            self.__logger.info("output to file: {}".format(out_filepath))

        empty_memory_cache()

        return {
            BASE64IMAGE: image_to_base64(result.images[0]),
            KEY_SEED.lower(): str(seed),
            KEY_WIDTH.lower(): config.get_width(),
            KEY_HEIGHT.lower(): config.get_height(),
            KEY_STEPS.lower(): config.get_steps(),
        }
