import torch
from typing import Union

from utilities.config import Config
from utilities.images import save_image
from utilities.logger import DummyLogger
from utilities.memory import empty_memory_cache
from utilities.model import Model
from utilities.times import get_epoch_now
from utilities.images import image_to_base64


class Text2Img:
    """
    Text2Img class.
    """

    def __init__(
        self,
        model: Model,
        output_folder: str = "",
        logger: DummyLogger = DummyLogger(),
    ):
        self.model = model
        self.__output_folder = output_folder
        self.__logger = logger

    def brunch(self, prompt: str, negative_prompt: str = ""):
        self.breakfast()
        self.lunch(prompt, negative_prompt)

    def breakfast(self):
        pass

    def lunch(self, prompt: str, negative_prompt: str = "", config: Config = Config()) -> str:
        self.model.set_txt2img_scheduler(config.get_scheduler())

        t = get_epoch_now()
        seed = config.get_seed()
        generator = torch.Generator("cuda").manual_seed(seed)
        self.__logger.info("current seed: {}".format(seed))

        result = self.model.txt2img_pipeline(
            prompt=prompt,
            width=config.get_width(),
            height=config.get_height(),
            negative_prompt=negative_prompt,
            guidance_scale=config.get_guidance_scale(),
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

        return image_to_base64(result.images[0])
