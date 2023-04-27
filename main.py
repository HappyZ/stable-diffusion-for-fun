from utilities.constants import LOGGER_NAME
from utilities.logger import Logger
from utilities.model import Model
from utilities.config import Config
from utilities.text2img import Text2Img


def prepare(logger: Logger) -> [Model, Config]:
    # model candidates:
    # "runwayml/stable-diffusion-v1-5"
    # "CompVis/stable-diffusion-v1-4"
    # "stabilityai/stable-diffusion-2-1"
    # "SG161222/Realistic_Vision_V2.0"
    # "darkstorm2150/Protogen_x3.4_Official_Release"
    # "prompthero/openjourney"
    # "naclbit/trinart_stable_diffusion_v2"
    # "hakurei/waifu-diffusion"
    model_name = "darkstorm2150/Protogen_x3.4_Official_Release"
    # inpainting model candidates:
    # "runwayml/stable-diffusion-inpainting"
    inpainting_model_name = "runwayml/stable-diffusion-inpainting"

    model = Model(model_name, inpainting_model_name, logger)
    model.reduce_memory()
    model.load()

    config = Config()
    return model, config


def main():
    logger = Logger(name=LOGGER_NAME)

    model, config = prepare(logger)
    text2img = Text2Img(model, config)

    input("confirm...")


if __name__ == "__main__":
    main()
