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
    model.set_low_memory_mode()
    model.load_all()

    config = Config()
    config.set_output_folder("/tmp/")
    return model, config


def main():
    logger = Logger(name=LOGGER_NAME)

    model, config = prepare(logger)
    text2img = Text2Img(model, config)

    text2img.breakfast()

    while True:
        try:
            prompt = input("Write prompt: ")
            if not prompt:
                prompt = "man riding a horse in space"
            negative_prompt = input("Write negative prompt: ")
            if not negative_prompt:
                negative_prompt = "(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime:1.4), text, close up, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck"
            text2img.lunch(prompt=prompt, negative_prompt=negative_prompt)
        except KeyboardInterrupt:
            break
        except BaseException:
            raise


if __name__ == "__main__":
    main()
