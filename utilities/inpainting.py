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


class Inpainting:
    """
    Inpainting class.
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
        mask_image: Union[Image.Image, None, str] = None,
        config: Config = Config(),
    ) -> dict:
        if not prompt:
            self.__logger.error("no prompt provided, won't proceed")
            return {}
        if reference_image is None:
            return {}
        if mask_image is None:
            return {}

        self.model.set_inpaint_scheduler(config.get_scheduler())

        t = get_epoch_now()
        seed = config.get_seed()
        generator = torch.Generator(self.__device).manual_seed(seed)
        self.__logger.info("current seed: {}".format(seed))

        if isinstance(reference_image, str):
            reference_image = base64_to_image(reference_image).convert("RGB")
            reference_image.thumbnail((config.get_width(), config.get_height()))

        if isinstance(mask_image, str):
            mask_image = base64_to_image(mask_image).convert("RGB")
            # assume mask image and reference image size ratio is the same
            if mask_image.size[0] < reference_image.size[0]:
                mask_image = mask_image.resize(reference_image.size)
            elif mask_image.size[0] > reference_image.size[0]:
                mask_image = mask_image.resize(reference_image.size, resample=Image.LANCZOS)

        result = self.model.inpaint_pipeline(
            prompt=prompt,
            image=reference_image.resize((512, 512)),  # must use size 512 for inpaint model
            mask_image=mask_image.convert("L").resize((512, 512)),  # must use size 512 for inpaint model
            negative_prompt=negative_prompt,
            guidance_scale=config.get_guidance_scale(),
            num_inference_steps=config.get_steps(),
            generator=generator,
            callback=None,
            callback_steps=10,
        )

        # resize it back based on ratio (keep width 512)
        result_img = result.images[0].resize((512, int(512 * reference_image.size[1] / reference_image.size[0])))

        if self.__output_folder:
            out_filepath = "{}/{}.png".format(self.__output_folder, t)
            result_img.save(out_filepath)
            self.__logger.info("output to file: {}".format(out_filepath))

        empty_memory_cache()

        return {
            BASE64IMAGE: image_to_base64(result_img),
            KEY_SEED: str(seed),
            KEY_WIDTH: config.get_width(),
            KEY_HEIGHT: config.get_height(),
            KEY_STEPS: config.get_steps(),
        }
