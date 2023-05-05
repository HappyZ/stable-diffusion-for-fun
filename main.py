import argparse
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

from utilities.constants import APIKEY
from utilities.constants import KEY_APP
from utilities.constants import KEY_JOB_STATUS
from utilities.constants import KEY_JOB_TYPE
from utilities.constants import KEY_PROMPT
from utilities.constants import KEY_NEG_PROMPT
from utilities.constants import LOGGER_NAME
from utilities.constants import LOGGER_NAME_IMG2IMG
from utilities.constants import LOGGER_NAME_TXT2IMG
from utilities.constants import REFERENCE_IMG
from utilities.constants import MAX_JOB_NUMBER
from utilities.constants import OPTIONAL_KEYS
from utilities.constants import REQUIRED_KEYS
from utilities.constants import UUID
from utilities.constants import VALUE_APP
from utilities.constants import VALUE_JOB_TXT2IMG
from utilities.constants import VALUE_JOB_IMG2IMG
from utilities.constants import VALUE_JOB_INPAINTING
from utilities.constants import VALUE_JOB_PENDING
from utilities.constants import VALUE_JOB_RUNNING
from utilities.constants import VALUE_JOB_DONE
from utilities.constants import VALUE_JOB_FAILED
from utilities.database import Database
from utilities.envvar import get_env_var_with_default
from utilities.envvar import get_env_var
from utilities.times import wait_for_seconds
from utilities.logger import Logger
from utilities.model import Model
from utilities.config import Config
from utilities.text2img import Text2Img
from utilities.img2img import Img2Img


app = Flask(__name__)
memory_lock = Lock()
event_termination = Event()
logger = Logger(name=LOGGER_NAME)
database = Database(logger)
use_gpu = True

local_job_stack = []
local_completed_jobs = []


@app.route("/add_job", methods=["POST"])
def add_job():
    req = request.get_json()

    if APIKEY not in req:
        logger.error(f"{APIKEY} not present in {req}")
        return "", 401
    with memory_lock:
        user = database.validate_user(req[APIKEY])
    if not user:
        logger.error(f"user not found with {req[APIKEY]}")
        return "", 401

    for key in req.keys():
        if (key not in REQUIRED_KEYS) and (key not in OPTIONAL_KEYS):
            return jsonify({"msg": "provided one or more unrecognized keys"}), 404
    for required_key in REQUIRED_KEYS:
        if required_key not in req:
            return jsonify({"msg": "missing one or more required keys"}), 404

    if req[KEY_JOB_TYPE] == VALUE_JOB_IMG2IMG and REFERENCE_IMG not in req:
        return jsonify({"msg": "missing reference image"}), 404

    if database.count_all_pending_jobs(req[APIKEY]) > MAX_JOB_NUMBER:
        return (
            jsonify({"msg": "too many jobs in queue, please wait or cancel some"}),
            500,
        )

    job_uuid = str(uuid.uuid4())
    logger.info("adding a new job with uuid {}..".format(job_uuid))

    with memory_lock:
        database.insert_new_job(req, job_uuid=job_uuid)

    return jsonify({"msg": "", UUID: job_uuid})


@app.route("/cancel_job", methods=["POST"])
def cancel_job():
    req = request.get_json()
    if APIKEY not in req:
        return "", 401
    with memory_lock:
        user = database.validate_user(req[APIKEY])
    if not user:
        return "", 401

    if UUID not in req:
        return jsonify({"msg": "missing uuid"}), 404

    logger.info("cancelling job with uuid {}..".format(req[UUID]))

    with memory_lock:
        result = database.cancel_job(job_uuid=req[UUID])

    if result:
        msg = "job with uuid {} removed".format(req[UUID])
        return jsonify({"msg": msg})

    with memory_lock:
        jobs = database.get_jobs(job_uuid=req[UUID])

    if jobs:
        return (
            jsonify(
                {
                    "msg": "job {} is not in pending state, unable to cancel".format(
                        req[UUID]
                    )
                }
            ),
            405,
        )

    return (
        jsonify({"msg": "unable to find the job with uuid {}".format(req[UUID])}),
        404,
    )


@app.route("/get_jobs", methods=["POST"])
def get_jobs():
    req = request.get_json()
    if APIKEY not in req:
        return "", 401
    with memory_lock:
        user = database.validate_user(req[APIKEY])
    if not user:
        return "", 401

    with memory_lock:
        jobs = database.get_jobs(job_uuid=req[UUID])

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


def backend(event_termination, db):
    model = load_model(logger)
    text2img = Text2Img(model, logger=Logger(name=LOGGER_NAME_TXT2IMG))
    img2img = Img2Img(model, logger=Logger(name=LOGGER_NAME_IMG2IMG))

    text2img.breakfast()
    img2img.breakfast()

    while not event_termination.is_set():
        wait_for_seconds(1)

        with memory_lock:
            pending_jobs = database.get_all_pending_jobs()

        if len(pending_jobs) == 0:
            continue

        next_job = pending_jobs[0]

        with memory_lock:
            database.update_job({KEY_JOB_STATUS: VALUE_JOB_RUNNING}, job_uuid=next_job[UUID])

        prompt = next_job[KEY_PROMPT]
        negative_prompt = next_job[KEY_NEG_PROMPT]

        config = Config().set_config(next_job)

        try:
            if next_job[KEY_JOB_TYPE] == VALUE_JOB_TXT2IMG:
                result_dict = text2img.lunch(
                    prompt=prompt, negative_prompt=negative_prompt, config=config
                )
            elif next_job[KEY_JOB_TYPE] == VALUE_JOB_IMG2IMG:
                ref_img = next_job[REFERENCE_IMG]
                result_dict = img2img.lunch(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    reference_image=ref_img,
                    config=config,
                )
        except BaseException as e:
            logger.error("text2img.lunch error: {}".format(e))
            with memory_lock:
                database.update_job(
                    {KEY_JOB_STATUS: VALUE_JOB_FAILED}, job_uuid=next_job[UUID]
                )
            continue

        with memory_lock:
            database.update_job({KEY_JOB_STATUS: VALUE_JOB_DONE}, job_uuid=next_job[UUID])
            database.update_job(result_dict, job_uuid=next_job[UUID])

    logger.critical("stopped")


def main(db_filepath, is_testing: bool = False):
    database.connect(db_filepath)

    if is_testing:
        try:
            app.run(host="0.0.0.0", port="5000")
        except KeyboardInterrupt:
            pass
        return
    thread = Thread(
        target=backend,
        args=(
            event_termination,
            database,
        ),
    )
    thread.start()
    # ugly solution for now
    # TODO: use a database to track instead of internal memory
    try:
        app.run(host="0.0.0.0", port="8888")
        thread.join()
    except KeyboardInterrupt:
        event_termination.set()

    database.safe_disconnect()

    thread.join(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Add an argument to set the 'testing' flag
    parser.add_argument("--testing", action="store_true", help="Enable testing mode")

    # Add an argument to set the path of the database file
    parser.add_argument(
        "--db", type=str, default="happysd.db", help="Path to SQLite database file"
    )

    args = parser.parse_args()
    logger.info(args)

    main(args.db, args.testing)
