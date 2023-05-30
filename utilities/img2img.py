import torch
import re
from typing import Union
from PIL import Image

from utilities.constants import BASE64IMAGE
from utilities.constants import KEY_SEED
from utilities.constants import KEY_WIDTH
from utilities.constants import KEY_HEIGHT
from utilities.constants import KEY_STEPS
from utilities.constants import KEY_BASE_MODEL
from utilities.config import Config
from utilities.logger import DummyLogger
from utilities.memory import empty_memory_cache
from utilities.model import Model
from utilities.times import get_epoch_now
from utilities.images import image_to_base64
from utilities.images import load_image
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
        self.__max_length = self.model.img2img_pipeline.tokenizer.model_max_length
        self.__logger.info(f"model has max length of {self.__max_length}")

    def __token_limit_workaround(self, prompt: str, negative_prompt: str = ""):
        token_est_count_prompt = len(prompt) / 4
        token_est_count_neg_prompt = len(negative_prompt) / 4

        if token_est_count_prompt < 77 and token_est_count_neg_prompt < 77:
            return prompt, None, negative_prompt, None

        self.__logger.info(
            "using workaround to generate embeds instead of direct string"
        )

        if token_est_count_prompt >= token_est_count_neg_prompt:
            input_ids = self.model.img2img_pipeline.tokenizer(
                prompt, return_tensors="pt", truncation=False
            ).input_ids.to(self.__device)
            shape_max_length = input_ids.shape[-1]
            negative_ids = self.model.img2img_pipeline.tokenizer(
                negative_prompt,
                truncation=False,
                padding="max_length",
                max_length=shape_max_length,
                return_tensors="pt",
            ).input_ids.to(self.__device)

        else:
            negative_ids = self.model.img2img_pipeline.tokenizer(
                negative_prompt, return_tensors="pt", truncation=False
            ).input_ids.to(self.__device)
            shape_max_length = negative_ids.shape[-1]
            input_ids = self.model.img2img_pipeline.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=False,
                padding="max_length",
                max_length=shape_max_length,
            ).input_ids.to(self.__device)

        concat_embeds = []
        neg_embeds = []
        for i in range(0, shape_max_length, self.__max_length):
            concat_embeds.append(
                self.model.img2img_pipeline.text_encoder(
                    input_ids[:, i : i + self.__max_length]
                )[0]
            )
            neg_embeds.append(
                self.model.img2img_pipeline.text_encoder(
                    negative_ids[:, i : i + self.__max_length]
                )[0]
            )

        return None, torch.cat(concat_embeds, dim=1), None, torch.cat(neg_embeds, dim=1)

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
            if "base64" in reference_image:
                reference_image = base64_to_image(reference_image).convert("RGB")
            else:
                # is filepath
                reference_image = load_image(reference_image).convert("RGB")
            reference_image.thumbnail((config.get_width(), config.get_height()))

        (
            prompt,
            prompt_embeds,
            negative_prompt,
            negative_prompt_embeds,
        ) = self.__token_limit_workaround(prompt, negative_prompt)

        result = self.model.img2img_pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            prompt_embeds=prompt_embeds,
            negative_prompt_embeds=negative_prompt_embeds,
            image=reference_image,
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
            KEY_SEED: str(seed),
            KEY_WIDTH: config.get_width(),
            KEY_HEIGHT: config.get_height(),
            KEY_STEPS: config.get_steps(),
            KEY_BASE_MODEL: self.model.model_name,
        }
