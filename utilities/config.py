import random
import time

from utilities.constants import KEY_GUIDANCE_SCALE
from utilities.constants import VALUE_GUIDANCE_SCALE_DEFAULT
from utilities.constants import KEY_HEIGHT
from utilities.constants import VALUE_HEIGHT_DEFAULT
from utilities.constants import KEY_PREVIEW
from utilities.constants import VALUE_PREVIEW_DEFAULT
from utilities.constants import KEY_SCHEDULER
from utilities.constants import VALUE_SCHEDULER_DEFAULT
from utilities.constants import VALUE_SCHEDULER_DDIM
from utilities.constants import VALUE_SCHEDULER_DPM_SOLVER_MULTISTEP
from utilities.constants import VALUE_SCHEDULER_EULER_DISCRETE
from utilities.constants import VALUE_SCHEDULER_LMS_DISCRETE
from utilities.constants import VALUE_SCHEDULER_PNDM
from utilities.constants import KEY_SEED
from utilities.constants import VALUE_SEED_DEFAULT
from utilities.constants import KEY_STEPS
from utilities.constants import VALUE_STEPS_DEFAULT
from utilities.constants import KEY_WIDTH
from utilities.constants import VALUE_WIDTH_DEFAULT
from utilities.logger import DummyLogger


class Config:
    """
    Configuration.
    """

    def __init__(self, logger: DummyLogger = DummyLogger()):
        self.__logger = logger
        self.__config = {}

    def get_config(self) -> dict:
        return self.__config

    def get_guidance_scale(self) -> float:
        return self.__config.get(KEY_GUIDANCE_SCALE, VALUE_GUIDANCE_SCALE_DEFAULT)

    def set_guidance_scale(self, scale: float):
        self.__logger.info("{} changed from {} to {}".format(KEY_GUIDANCE_SCALE, self.get_guidance_scale(), scale))
        self.__config[KEY_GUIDANCE_SCALE] = scale

    def get_height(self) -> int:
        return self.__config.get(KEY_HEIGHT, VALUE_HEIGHT_DEFAULT)

    def set_height(self, value: int):
        self.__logger.info("{} changed from {} to {}".format(KEY_HEIGHT, self.get_height(), value))
        self.__config[KEY_HEIGHT] = value

    def get_preview(self) -> bool:
        return self.__config.get(KEY_PREVIEW, VALUE_PREVIEW_DEFAULT)

    def set_preview(self, boolean: bool):
        self.__logger.info("{} changed from {} to {}".format(KEY_PREVIEW, self.get_preview(), boolean))
        self.__config[KEY_PREVIEW] = boolean

    def get_scheduler(self) -> str:
        return self.__config.get(KEY_SCHEDULER, VALUE_SCHEDULER_DEFAULT)

    def set_scheduler(self, scheduler: str):
        if not scheduler:
            scheduler = VALUE_SCHEDULER_DEFAULT
        self.__logger.info("{} changed from {} to {}".format(KEY_SCHEDULER, self.get_scheduler(), scheduler))
        self.__config[KEY_SCHEDULER] = scheduler

    def get_seed(self) -> int:
        seed = self.__config.get(KEY_SEED, VALUE_SEED_DEFAULT)
        if seed == 0:
            random.seed(int(time.time_ns()))
            seed = random.getrandbits(64)
        return seed

    def set_seed(self, seed: int):
        self.__logger.info("{} changed from {} to {}".format(KEY_SEED, self.get_seed(), seed))
        self.__config[KEY_SEED] = seed

    def get_steps(self) -> int:
        return self.__config.get(KEY_STEPS, VALUE_STEPS_DEFAULT)

    def set_steps(self, steps: int):
        self.__logger.info("{} changed from {} to {}".format(KEY_STEPS, self.get_steps(), steps))
        self.__config[KEY_STEPS] = steps

    def get_width(self) -> int:
        return self.__config.get(KEY_WIDTH, VALUE_WIDTH_DEFAULT)

    def set_width(self, value: int):
        self.__logger.info("{} changed from {} to {}".format(KEY_WIDTH, self.get_width(), value))
        self.__config[KEY_WIDTH] = value
