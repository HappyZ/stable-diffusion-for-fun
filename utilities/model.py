import os
from io import BytesIO
import requests
import diffusers
import torch
from diffusers import StableDiffusionPipeline
from diffusers import StableDiffusionImg2ImgPipeline
from diffusers import StableDiffusionInpaintPipeline
from diffusers.pipelines.stable_diffusion.convert_from_ckpt import (
    download_from_original_stable_diffusion_ckpt,
)

from utilities.constants import VALUE_SCHEDULER_DEFAULT
from utilities.constants import VALUE_SCHEDULER_DDIM
from utilities.constants import VALUE_SCHEDULER_DPM_SOLVER_MULTISTEP
from utilities.constants import VALUE_SCHEDULER_EULER_DISCRETE
from utilities.constants import VALUE_SCHEDULER_LMS_DISCRETE
from utilities.constants import VALUE_SCHEDULER_PNDM
from utilities.logger import DummyLogger
from utilities.memory import empty_memory_cache
from utilities.memory import tune_for_low_memory


def download_model(url, output_folder):
    filepath = f"{output_folder}/{os.path.basename(url)}"
    if os.path.isfile(filepath):
        return filepath

    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    block_size = 1048576  # 1 MB
    downloaded_size = 0

    with open(filepath, "wb") as file:
        for data in response.iter_content(block_size):
            downloaded_size += len(data)
            file.write(data)
            # Calculate the progress
            progress = downloaded_size / total_size * 100
            print(f"Download progress: {progress:.2f}%")
    return filepath


class Model:
    """Model class."""

    def __init__(
        self,
        model_name: str,
        inpainting_model_name: str,
        logger: DummyLogger = DummyLogger(),
        use_gpu: bool = True,
        gpu_device_name: str = "cuda",
        model_caching_folder_path: str = "/tmp",
    ):
        self.model_name = model_name
        self.inpainting_model_name = inpainting_model_name
        self.__use_gpu = False
        self.__gpu_device = gpu_device_name
        if use_gpu and torch.cuda.is_available():
            self.__use_gpu = True
            logger.info(
                "running on {}".format(torch.cuda.get_device_name(self.__gpu_device))
            )
        else:
            logger.info("running on CPU (expect it to be verrry sloooow)")
        self.__logger = logger
        self.__torch_dtype = torch.float64
        self.__model_caching_folder_path = model_caching_folder_path

        # txt2img and img2img are always loaded together
        self.txt2img_pipeline = None
        self.img2img_pipeline = None
        self.inpaint_pipeline = None

    def use_gpu(self):
        return self.__use_gpu

    def get_gpu_device_name(self):
        return self.__gpu_device

    def update_model_name(self, model_name: str):
        if not model_name or model_name == self.model_name:
            self.__logger.warn("model name empty or the same, not updated")
            return
        self.model_name = model_name
        self.load_txt2img_and_img2img_pipeline(force_reload=True)

    def set_low_memory_mode(self):
        self.__logger.info("reduces memory usage by using float16 dtype")
        tune_for_low_memory()
        self.__torch_dtype = torch.float16

    def __set_scheduler(self, scheduler: str, pipeline, default_scheduler):
        if scheduler == VALUE_SCHEDULER_DEFAULT:
            pipeline.scheduler = default_scheduler
            return
        config = pipeline.scheduler.config
        pipeline.scheduler = getattr(diffusers, scheduler).from_config(config)

        empty_memory_cache()

    def set_img2img_scheduler(self, scheduler: str):
        # note the change here also affects txt2img scheduler
        if self.img2img_pipeline is None:
            self.__logger.error("no img2img pipeline loaded, unable to set scheduler")
            return
        self.__set_scheduler(
            scheduler, self.img2img_pipeline, self.__default_img2img_scheduler
        )

    def set_txt2img_scheduler(self, scheduler: str):
        # note the change here also affects img2img scheduler
        if self.txt2img_pipeline is None:
            self.__logger.error("no txt2img pipeline loaded, unable to set scheduler")
            return
        self.__set_scheduler(
            scheduler, self.txt2img_pipeline, self.__default_txt2img_scheduler
        )

    def set_inpaint_scheduler(self, scheduler: str):
        if self.inpaint_pipeline is None:
            self.__logger.error("no inpaint pipeline loaded, unable to set scheduler")
            return
        self.__set_scheduler(
            scheduler, self.inpaint_pipeline, self.__default_inpaint_scheduler
        )

    def load_txt2img_and_img2img_pipeline(self, force_reload: bool = False):
        if (not force_reload) and (self.txt2img_pipeline is not None):
            self.__logger.warn("txt2img and img2img pipelines already loaded")
            return
        if not self.model_name:
            self.__logger.error(
                "unable to load txt2img and img2img pipelines, model not set"
            )
            return
        revision = get_revision_from_model_name(self.model_name)
        pipeline = None
        try:
            pipeline = StableDiffusionPipeline.from_pretrained(
                model_name,
                revision=revision,
                torch_dtype=self.__torch_dtype,
                safety_checker=None,
            )
        except:
            try:
                pipeline = StableDiffusionPipeline.from_pretrained(
                    self.model_name,
                    torch_dtype=self.__torch_dtype,
                    safety_checker=None,
                )
            except Exception as e:
                self.__logger.error(
                    "failed to load model %s: %s" % (self.model_name, e)
                )
        if pipeline and self.use_gpu():
            pipeline.to(self.get_gpu_device_name())

        self.txt2img_pipeline = pipeline
        self.__default_txt2img_scheduler = pipeline.scheduler

        self.img2img_pipeline = StableDiffusionImg2ImgPipeline(**pipeline.components)
        self.__default_img2img_scheduler = self.__default_txt2img_scheduler

        empty_memory_cache()

    def load_inpaint_pipeline(self, force_reload: bool = False):
        if (not force_reload) and (self.inpaint_pipeline is not None):
            self.__logger.warn("inpaint pipeline already loaded")
            return
        if not self.inpainting_model_name:
            self.__logger.error("unable to load inpaint pipeline, model not set")
            return

        pipeline = None

        _, extension = os.path.splitext(self.inpainting_model_name)
        if extension.lower() == ".ckpt":
            if not os.path.isfile(self.inpainting_model_name):
                model_filepath = download_model(
                    self.inpainting_model_name, self.__model_caching_folder_path
                )
            else:
                model_filepath = self.inpainting_model_name
            original_config_file = BytesIO(requests.get("https://raw.githubusercontent.com/runwayml/stable-diffusion/main/configs/stable-diffusion/v1-inpainting-inference.yaml").content)
            pipeline = download_from_original_stable_diffusion_ckpt(
                model_filepath,
                original_config_file=original_config_file,
                load_safety_checker=False,
                pipeline_class=StableDiffusionInpaintPipeline,
                device="cpu" if not self.use_gpu() else self.get_gpu_device_name(),
            )
        elif extension.lower() == ".safetensors":
            if not os.path.isfile(self.inpainting_model_name):
                model_filepath = download_model(
                    self.inpainting_model_name, self.__model_caching_folder_path
                )
            else:
                model_filepath = self.inpainting_model_name
            original_config_file = BytesIO(requests.get("https://raw.githubusercontent.com/runwayml/stable-diffusion/main/configs/stable-diffusion/v1-inpainting-inference.yaml").content)
            pipeline = download_from_original_stable_diffusion_ckpt(
                model_filepath,
                original_config_file=original_config_file,
                from_safetensors=True,
                load_safety_checker=False,
                pipeline_class=StableDiffusionInpaintPipeline,
                device="cpu" if not self.use_gpu() else self.get_gpu_device_name(),
            )
        else:
            revision = get_revision_from_model_name(self.inpainting_model_name)
            try:
                pipeline = StableDiffusionInpaintPipeline.from_pretrained(
                    self.inpainting_model_name,
                    revision=revision,
                    torch_dtype=self.__torch_dtype,
                    safety_checker=None,
                )
            except:
                try:
                    pipeline = StableDiffusionInpaintPipeline.from_pretrained(
                        self.inpainting_model_name,
                        torch_dtype=self.__torch_dtype,
                        safety_checker=None,
                    )
                except Exception as e:
                    self.__logger.error(
                        "failed to load inpaint model %s: %s"
                        % (self.inpainting_model_name, e)
                    )
        if pipeline:
            if self.use_gpu():
                pipeline.to(self.get_gpu_device_name())
            self.inpaint_pipeline = pipeline
            self.__default_inpaint_scheduler = pipeline.scheduler
        empty_memory_cache()

    def load_all(self):
        self.load_txt2img_and_img2img_pipeline()
        self.load_inpaint_pipeline()


def get_revision_from_model_name(model_name: str):
    return (
        "diffusers-115k"
        if model_name == "naclbit/trinart_stable_diffusion_v2"
        else "fp16"
    )
