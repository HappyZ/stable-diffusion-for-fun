import copy
import tempfile
import pkgutil
import uuid
from flask import jsonify
from flask import Flask
from flask import render_template
from flask import request
from threading import Event
from threading import Thread
from threading import Lock

from utilities.constants import API_KEY
from utilities.constants import API_KEY_FOR_DEMO
from utilities.constants import KEY_APP
from utilities.constants import KEY_JOB_STATUS
from utilities.constants import KEY_PROMPT
from utilities.constants import KEY_NEG_PROMPT
from utilities.constants import LOGGER_NAME
from utilities.constants import MAX_JOB_NUMBER
from utilities.constants import OPTIONAL_KEYS
from utilities.constants import REQUIRED_KEYS
from utilities.constants import UUID
from utilities.constants import VALUE_APP
from utilities.constants import VALUE_JOB_PENDING
from utilities.constants import VALUE_JOB_RUNNING
from utilities.constants import VALUE_JOB_DONE
from utilities.constants import VALUE_JOB_FAILED
from utilities.envvar import get_env_var_with_default
from utilities.envvar import get_env_var
from utilities.times import wait_for_seconds
from utilities.logger import Logger
from utilities.model import Model
from utilities.config import Config
from utilities.text2img import Text2Img


app = Flask(__name__)
fast_web_debugging = False
memory_lock = Lock()
event_termination = Event()
logger = Logger(name=LOGGER_NAME)
use_gpu = True

local_job_stack = []
local_completed_jobs = []


@app.route("/add_job", methods=["POST"])
def add_job():
    req = request.get_json()
    if API_KEY not in req:
        return "", 401
    if get_env_var_with_default(KEY_APP, VALUE_APP) == VALUE_APP:
        if req[API_KEY] != API_KEY_FOR_DEMO:
            return "", 401
    else:
        # TODO: add logic to validate app key with a particular user
        return "", 401

    for key in req.keys():
        if (key not in REQUIRED_KEYS) and (key not in OPTIONAL_KEYS):
            return jsonify({"msg": "provided one or more unrecognized keys"}), 404
    for required_key in REQUIRED_KEYS:
        if required_key not in req:
            return jsonify({"msg": "missing one or more required keys"}), 404

    if len(local_job_stack) > MAX_JOB_NUMBER:
        return jsonify({"msg": "too many jobs in queue, please wait"}), 500

    req[UUID] = str(uuid.uuid4())
    logger.info("adding a new job with uuid {}..".format(req[UUID]))

    req[KEY_JOB_STATUS] = VALUE_JOB_PENDING
    req["position"] = len(local_job_stack) + 1

    with memory_lock:
        local_job_stack.append(req)

    return jsonify({"msg": "", "position": req["position"], UUID: req[UUID]})


@app.route("/cancel_job", methods=["POST"])
def cancel_job():
    req = request.get_json()
    if API_KEY not in req:
        return "", 401
    if get_env_var_with_default(KEY_APP, VALUE_APP) == VALUE_APP:
        if req[API_KEY] != API_KEY_FOR_DEMO:
            return "", 401
    else:
        # TODO: add logic to validate app key with a particular user
        return "", 401

    if UUID not in req:
        return jsonify({"msg": "missing uuid"}), 404

    logger.info("removing job with uuid {}..".format(req[UUID]))

    cancel_job_position = None
    with memory_lock:
        for job_position in range(len(local_job_stack)):
            if local_job_stack[job_position][UUID] == req[UUID]:
                cancel_job_position = job_position
                break
        logger.info("foud {}".format(cancel_job_position))
        if cancel_job_position is not None:
            if local_job_stack[cancel_job_position][API_KEY] != req[API_KEY]:
                return "", 401
            if (
                local_job_stack[cancel_job_position][KEY_JOB_STATUS]
                == VALUE_JOB_RUNNING
            ):
                logger.info(
                    "job at {} with uuid {} is running and cannot be cancelled".format(
                        cancel_job_position, req[UUID]
                    )
                )
                return (
                    jsonify(
                        {
                            "msg": "job {} is already running, unable to cancel".format(
                                req[UUID]
                            )
                        }
                    ),
                    405,
                )
            del local_job_stack[cancel_job_position]
            msg = "job with uuid {} removed".format(req[UUID])
            logger.info(msg)
            return jsonify({"msg": msg})
    return (
        jsonify({"msg": "unable to find the job with uuid {}".format(req[UUID])}),
        404,
    )


@app.route("/get_jobs", methods=["POST"])
def get_jobs():
    req = request.get_json()
    if API_KEY not in req:
        return "", 401
    if get_env_var_with_default(KEY_APP, VALUE_APP) == VALUE_APP:
        if req[API_KEY] != API_KEY_FOR_DEMO:
            return "", 401
    else:
        # TODO: add logic to validate app key with a particular user
        return "", 401

    jobs = []

    all_job_stack = local_job_stack + local_completed_jobs
    with memory_lock:
        for job_position in range(len(all_job_stack)):
            # filter on API_KEY
            if all_job_stack[job_position][API_KEY] != req[API_KEY]:
                continue
            # filter on UUID
            if UUID in req and req[UUID] != all_job_stack[job_position][UUID]:
                continue
            job = copy.deepcopy(all_job_stack[job_position])
            if job[KEY_JOB_STATUS] == VALUE_JOB_DONE:
                del job["position"]
            del job[API_KEY]
            jobs.append(job)

    if len(jobs) == 0:
        return (
            jsonify({"msg": "found no jobs for api_key={}".format(req[API_KEY])}),
            404,
        )
    return jsonify({"jobs": jobs})


@app.route("/")
def index():
    return render_template("index.html")


def load_model(logger: Logger) -> Model:
    # model candidates:
    # "runwayml/stable-diffusion-v1-5"
    # "CompVis/stable-diffusion-v1-4"
    # "stabilityai/stable-diffusion-2-1"
    # "SG161222/Realistic_Vision_V2.0"
    # "darkstorm2150/Protogen_x3.4_Official_Release"
    # "darkstorm2150/Protogen_x5.8_Official_Release"
    # "prompthero/openjourney"
    # "naclbit/trinart_stable_diffusion_v2"
    # "hakurei/waifu-diffusion"
    model_name = "darkstorm2150/Protogen_x5.8_Official_Release"
    # inpainting model candidates:
    # "runwayml/stable-diffusion-inpainting"
    inpainting_model_name = "runwayml/stable-diffusion-inpainting"

    model = Model(model_name, inpainting_model_name, logger, use_gpu=use_gpu)
    if use_gpu:
        model.set_low_memory_mode()
    model.load_all()

    return model


def backend(event_termination):
    model = load_model(logger)
    text2img = Text2Img(model, logger=logger)

    text2img.breakfast()

    while not event_termination.is_set():
        wait_for_seconds(1)

        with memory_lock:
            if len(local_job_stack) == 0:
                continue
            next_job = local_job_stack[0]
            next_job[KEY_JOB_STATUS] = VALUE_JOB_RUNNING

            prompt = next_job[KEY_PROMPT.lower()]
            negative_prompt = next_job.get(KEY_NEG_PROMPT.lower(), "")

            config = Config().set_config(next_job)

        try:
            result_dict = text2img.lunch(
                prompt=prompt, negative_prompt=negative_prompt, config=config
            )
        except BaseException as e:
            logger.error("text2img.lunch error: {}".format(e))
            local_job_stack.pop(0)
            next_job[KEY_JOB_STATUS] = VALUE_JOB_FAILED
            local_completed_jobs.append(next_job)

        with memory_lock:
            local_job_stack.pop(0)
            next_job[KEY_JOB_STATUS] = VALUE_JOB_DONE
            next_job.update(result_dict)
            local_completed_jobs.append(next_job)

    logger.critical("stopped")
    if len(local_job_stack) > 0:
        logger.info(
            "remaining {} jobs in stack: {}".format(
                len(local_job_stack), local_job_stack
            )
        )


def main():
    if fast_web_debugging:
        try:
            app.run(host="0.0.0.0")
        except KeyboardInterrupt:
            pass
        return
    thread = Thread(target=backend, args=(event_termination,))
    thread.start()
    # ugly solution for now
    # TODO: use a database to track instead of internal memory
    try:
        app.run(host="0.0.0.0")
        thread.join()
    except KeyboardInterrupt:
        event_termination.set()
        thread.join(1)


if __name__ == "__main__":
    main()
