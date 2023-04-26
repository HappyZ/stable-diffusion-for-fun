from utilities.model import Model
from utilities.logger import Logger

def prepare(logger: Logger):
    model_name = "darkstorm2150/Protogen_x3.4_Official_Release"
    inpainting_model_name = "runwayml/stable-diffusion-inpainting"

    model = Model(model_name, inpainting_model_name, logger)
    model.reduce_memory()
    model.load()
    return model


def main():
    logger = Logger(name="rl_trader")

    model = prepare(logger)
    
    input("confirm...")


if __name__ == "__main__":
    main()
