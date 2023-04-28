import torch
from typing import Union

from utilities.config import Config
from utilities.images import save_image
from utilities.logger import DummyLogger
from utilities.memory import empty_memory_cache
from utilities.model import Model
from utilities.times import get_epoch_now


class Text2Img:
    """
    Text2Img class.
    """

    def __init__(
        self,
        model: Model,
        config: Union[Config, None],
        logger: DummyLogger = DummyLogger(),
    ):
        self.model = model
        self.config = config
        self.__logger = logger

    def update_config(self, config: Config):
        self.config = config
    
    def brunch(self, prompt: str, negative_prompt: str = ""):
        self.breakfast()
        self.lunch(prompt, negative_prompt)

    def breakfast(self):
        self.model.set_txt2img_scheduler(self.config.get_scheduler())
        
    def lunch(self, prompt: str, negative_prompt: str = ""):
        t = get_epoch_now()
        seed = self.config.get_seed()
        self.__logger.info("current seed: {}".format(seed))

        generator = torch.Generator("cuda").manual_seed(seed)

        result = self.model.txt2img_pipeline(
            prompt=prompt,
            width=self.config.get_width(),
            height=self.config.get_height(),
            negative_prompt=negative_prompt,
            guidance_scale=self.config.get_guidance_scale(),
            num_inference_steps=self.config.get_steps(),
            generator=generator,
            callback=None,
            callback_steps=10,
        )

        out_filepath = "{}/{}.png".format(self.config.get_output_folder(), t)
        result.images[0].save(out_filepath)

        self.__logger.info("output to file: {}".format(out_filepath))

        empty_memory_cache()
