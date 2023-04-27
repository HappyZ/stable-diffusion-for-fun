from utilities.config import Config
from utilities.model import Model


class Text2Img:
    """
    Text2Img class.
    """

    def __init__(self, model: Model, config: Config):
        self.model = model
        self.config = config

    def update_config(config: Config):
        self.config = config
    
    def update_model(model, Model):
        self.model = model
    
    