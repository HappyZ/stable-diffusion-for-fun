from utilities.config import Config
from utilities.model import Model


class Text2Img:
    """
    Text2Img class.
    """

    def __init__(self, model: Model, config: Config):
        self.model = model
        self.config = config

    def breakfast(self):
        self.model.set_txt2img_scheduler(config.get_scheduler())
