KEY_APP = "APP"
VALUE_APP = "demo"

LOGGER_NAME_FRONTEND = VALUE_APP + "_fe"
LOGGER_NAME_BACKEND = VALUE_APP + "_be"
LOGGER_NAME_TXT2IMG = VALUE_APP + "_txt2img"
LOGGER_NAME_IMG2IMG = VALUE_APP + "_img2img"
MAX_JOB_NUMBER = 10

LOCK_FILEPATH = "/tmp/happysd_db.lock"

KEY_OUTPUT_FOLDER = "outfolder"
VALUE_OUTPUT_FOLDER_DEFAULT = ""

#
# Database
#
HISTORY_TABLE_NAME = "history"
USERS_TABLE_NAME = "users"

#
# REST API Keys
#

# - input and output
APIKEY = "apikey"

KEY_JOB_TYPE = "type"
VALUE_JOB_TXT2IMG = "txt"  # default value for KEY_JOB_TYPE
VALUE_JOB_IMG2IMG = "img"
REFERENCE_IMG = "ref_img"
VALUE_JOB_INPAINTING = "inpaint"

KEY_LANGUAGE = "lang"
VALUE_LANGUAGE_ZH_CN = "zh_CN"
VALUE_LANGUAGE_EN = "en_XX"
KEY_PROMPT = "prompt"
KEY_NEG_PROMPT = "neg_prompt"
KEY_SEED = "seed"
VALUE_SEED_DEFAULT = 0  # default value for KEY_SEED
KEY_WIDTH = "width"
VALUE_WIDTH_DEFAULT = 512  # default value for KEY_WIDTH
KEY_HEIGHT = "height"
VALUE_HEIGHT_DEFAULT = 512  # default value for KEY_HEIGHT
KEY_GUIDANCE_SCALE = "guidance_scale"
VALUE_GUIDANCE_SCALE_DEFAULT = 12.5  # default value for KEY_GUIDANCE_SCALE
KEY_STEPS = "steps"
VALUE_STEPS_DEFAULT = 100  # default value for KEY_STEPS
KEY_SCHEDULER = "scheduler"
VALUE_SCHEDULER_DEFAULT = "Default"  # default value for KEY_SCHEDULER
VALUE_SCHEDULER_DPM_SOLVER_MULTISTEP = "DPMSolverMultistepScheduler"
VALUE_SCHEDULER_LMS_DISCRETE = "LMSDiscreteScheduler"
VALUE_SCHEDULER_EULER_DISCRETE = "EulerDiscreteScheduler"
VALUE_SCHEDULER_PNDM = "PNDMScheduler"
VALUE_SCHEDULER_DDIM = "DDIMScheduler"
KEY_STRENGTH = "strength"
VALUE_STRENGTH_DEFAULT = 0.5  # default value for KEY_STRENGTH

REQUIRED_KEYS = [
    APIKEY,  # str
    KEY_PROMPT,  # str
    KEY_JOB_TYPE,  # str
]
OPTIONAL_KEYS = [
    KEY_NEG_PROMPT,  # str
    KEY_SEED,  # str
    KEY_WIDTH,  # int
    KEY_HEIGHT,  # int
    KEY_GUIDANCE_SCALE,  # float
    KEY_STEPS,  # int
    KEY_SCHEDULER,  # str
    KEY_STRENGTH,  # float
    REFERENCE_IMG,  # str (base64)
    KEY_LANGUAGE,
]

# - output only
UUID = "uuid"
BASE64IMAGE = "img"
KEY_PRIORITY = "priority"
KEY_JOB_STATUS = "status"
VALUE_JOB_PENDING = "pending"  # default value for KEY_JOB_STATUS
VALUE_JOB_RUNNING = "running"
VALUE_JOB_DONE = "done"
VALUE_JOB_FAILED = "failed"

OUTPUT_ONLY_KEYS = [
    UUID,  # str
    KEY_PRIORITY,  # int
    BASE64IMAGE,  # str (base64)
    KEY_JOB_STATUS,  # str
]

SUPPORTED_LANGS = [
    VALUE_LANGUAGE_ZH_CN,
    VALUE_LANGUAGE_EN,
]