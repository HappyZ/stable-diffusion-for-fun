import torch
from diffusers import StableDiffusionPipeline
from diffusers import StableDiffusionImg2ImgPipeline
from diffusers import StableDiffusionInpaintPipeline

from utilities.logger import Logger
from utilities.memory import empty_memory
from utilities.memory import tune_for_low_memory

class Model():
    '''Model class.'''
    def __init__(self, model_name: str, inpainting_model_name: str, logger: Logger, use_gpu: bool=True):
        self.model_name = model_name
        self.inpainting_model_name = inpainting_model_name
        self.__use_gpu = False
        if use_gpu and torch.cuda.is_available():
            self.__use_gpu = True
            logger.info("running on {}".format(torch.cuda.get_device_name("cuda:0")))
        self.logger = logger
        self.sd_pipeline = None
        self.img2img_pipeline = None
        self.inpaint_pipeline = None
        self.__torch_dtype = "auto"

    def use_gpu(self):
        return self.__use_gpu

    def reduce_memory(self):
        self.logger.info("reduces memory usage by using float16 dtype")
        tune_for_low_memory()
        self.__torch_dtype = torch.float16

    def load(self):
        empty_memory()

        if self.model_name:
            revision = get_revision_from_model_name(self.model_name)
            sd_pipeline = None
            try:
                sd_pipeline = StableDiffusionPipeline.from_pretrained(
                    model_name,
                    revision=revision,
                    torch_dtype=self.__torch_dtype,
                    safety_checker=None)
            except:
                try:
                    sd_pipeline = StableDiffusionPipeline.from_pretrained(
                        self.model_name,
                        torch_dtype=self.__torch_dtype,
                        safety_checker=None)
                except Exception as e:
                    self.logger.error("failed to load model %s: %s" % (self.model_name, e))
            if sd_pipeline and self.use_gpu():
                sd_pipeline.to("cuda")
            self.sd_pipeline = sd_pipeline
            self.sd_pipeline_scheduler = sd_pipeline.scheduler

            self.img2img_pipeline = StableDiffusionImg2ImgPipeline(**sd_pipeline.components)

        if self.inpainting_model_name:
            revision = get_revision_from_model_name(self.inpainting_model_name)
            inpaint_pipeline = None
            try:
                inpaint_pipeline = StableDiffusionInpaintPipeline.from_pretrained(
                    model_name,
                    revision=revision,
                    torch_dtype=self.__torch_dtype,
                    safety_checker=None)
            except:
                try:
                    inpaint_pipeline = StableDiffusionInpaintPipeline.from_pretrained(
                        self.inpainting_model_name,
                        torch_dtype=self.__torch_dtype,
                        safety_checker=None)
                except Exception as e:
                    self.logger.error("failed to load inpaint model %s: %s" % (self.inpainting_model_name, e))
            if inpaint_pipeline and self.use_gpu():
                inpaint_pipeline.to("cuda")
            self.inpaint_pipeline = inpaint_pipeline
            self.inpaint_pipeline_scheduler = inpaint_pipeline.scheduler


def get_revision_from_model_name(model_name: str):
    return "diffusers-115k" if  model_name == "naclbit/trinart_stable_diffusion_v2" else "fp16"