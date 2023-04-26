import torch
from diffusers import StableDiffusionPipeline
from diffusers import StableDiffusionImg2ImgPipeline

from utilities.memory import empty_memory
from utilities.logger import Logger

def from_pretrained(model_name: str, logger: Logger):
    rev = "diffusers-115k" if  model_name == "naclbit/trinart_stable_diffusion_v2" else "fp16"

    pipe = None
    try:
        pipe = StableDiffusionPipeline.from_pretrained(model_name, revision=rev, torch_dtype=torch.float16, safety_checker=None)
        pipe.to("cuda")
    except:
        try:
            pipe = StableDiffusionPipeline.from_pretrained(model_name, torch_dtype=torch.float16, safety_checker=None)
            pipe.to("cuda")
        except Exception as e:
            logger.error("Failed to load model %s: %s" % (model_name, e))
    return pipe

def prepare(logger: Logger):
    empty_memory()

    torch.set_default_dtype(torch.float16)

    model_name = "darkstorm2150/Protogen_x3.4_Official_Release"

    if not torch.cuda.is_available():
        logger.error("no GPU found, will not proceed")
        return False
    
    logger.info("running on {}".format(torch.cuda.get_device_name("cuda:0")))

    logger.info("loading model: {}".format(model_name))
    pipeline = from_pretrained(model_name, logger)

    if pipeline is None:
        return False

    img2img = StableDiffusionImg2ImgPipeline(**pipeline.components)
    default_pipe_scheduler = pipeline.scheduler

    return True


def main():
    logger = Logger(name="rl_trader")

    if not prepare(logger):
        return
    
    input("confirm...")


if __name__ == "__main__":
    main()
