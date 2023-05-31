import diffusers
import torch
from diffusers import StableDiffusionPipeline
from diffusers import StableDiffusionImg2ImgPipeline
from diffusers import StableDiffusionInpaintPipeline

from utilities.constants import VALUE_SCHEDULER_DEFAULT
from utilities.constants import VALUE_SCHEDULER_DDIM
from utilities.constants import VALUE_SCHEDULER_DPM_SOLVER_MULTISTEP
from utilities.constants import VALUE_SCHEDULER_EULER_DISCRETE
from utilities.constants import VALUE_SCHEDULER_LMS_DISCRETE
from utilities.constants import VALUE_SCHEDULER_PNDM
from utilities.logger import DummyLogger
from utilities.memory import empty_memory_cache
from utilities.memory import tune_for_low_memory


class Model:
    """Model class."""

    def __init__(
        self,
        model_name: str,
        inpainting_model_name: str,
        logger: DummyLogger = DummyLogger(),
        use_gpu: bool = True,
    ):
        self.model_name = model_name
        self.inpainting_model_name = inpainting_model_name
        self.__use_gpu = False
        if use_gpu and torch.cuda.is_available():
            self.__use_gpu = True
            logger.info("running on {}".format(torch.cuda.get_device_name("cuda:0")))
        else:
            logger.info("running on CPU (expect it to be verrry sloooow)")
        self.__logger = logger
        self.__torch_dtype = torch.float64

        # txt2img and img2img are always loaded together
        self.txt2img_pipeline = None
        self.img2img_pipeline = None
        self.inpaint_pipeline = None

    def use_gpu(self):
        return self.__use_gpu
    
    def update_model_name(self, model_name:str):
        if not model_name or model_name == self.model_name:
            self.__logger.warn("model name empty or the same, not updated")
            return
        self.model_name = model_name
        self.load_txt2img_and_img2img_pipeline(force_reload=True)

    def set_low_memory_mode(self):
        self.__logger.info("reduces memory usage by using float16 dtype")
        tune_for_low_memory()
        self.__torch_dtype = torch.float16
    
    def __set_scheduler(self, scheduler:str, pipeline, default_scheduler):
        if scheduler == VALUE_SCHEDULER_DEFAULT:
            pipeline.scheduler = default_scheduler
            return
        config = pipeline.scheduler.config
        pipeline.scheduler = getattr(diffusers, scheduler).from_config(config)

        empty_memory_cache()

    def set_img2img_scheduler(self, scheduler:str):
        # note the change here also affects txt2img scheduler
        if self.img2img_pipeline is None:
            self.__logger.error("no img2img pipeline loaded, unable to set scheduler")
            return
        self.__set_scheduler(scheduler, self.img2img_pipeline, self.__default_img2img_scheduler)

    def set_txt2img_scheduler(self, scheduler:str):
        # note the change here also affects img2img scheduler
        if self.txt2img_pipeline is None:
            self.__logger.error("no txt2img pipeline loaded, unable to set scheduler")
            return
        self.__set_scheduler(scheduler, self.txt2img_pipeline, self.__default_txt2img_scheduler)

    def set_inpaint_scheduler(self, scheduler:str):
        if self.inpaint_pipeline is None:
            self.__logger.error("no inpaint pipeline loaded, unable to set scheduler")
            return
        self.__set_scheduler(scheduler, self.inpaint_pipeline, self.__default_inpaint_scheduler)
    
    def load_txt2img_and_img2img_pipeline(self, force_reload:bool=False):
        if (not force_reload) and (self.txt2img_pipeline is not None):
            self.__logger.warn("txt2img and img2img pipelines already loaded")
            return
        if not self.model_name:
            self.__logger.error("unable to load txt2img and img2img pipelines, model not set")
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
            pipeline.to("cuda")
            
        self.txt2img_pipeline = pipeline
        self.__default_txt2img_scheduler = pipeline.scheduler

        self.img2img_pipeline = StableDiffusionImg2ImgPipeline(
            **pipeline.components
        )
        self.__default_img2img_scheduler = self.__default_txt2img_scheduler

        empty_memory_cache()

    def load_inpaint_pipeline(self, force_reload:bool=False):
        if (not force_reload) and (self.inpaint_pipeline is not None):
            self.__logger.warn("inpaint pipeline already loaded")
            return
        if not self.inpainting_model_name:
            self.__logger.error("unable to load inpaint pipeline, model not set")
            return
        revision = get_revision_from_model_name(self.inpainting_model_name)
        pipeline = None
        try:
            pipeline = StableDiffusionInpaintPipeline.from_pretrained(
                model_name,
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
        if pipeline and self.use_gpu():
            pipeline.to("cuda")
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
