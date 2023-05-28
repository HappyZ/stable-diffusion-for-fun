import argparse
import uuid
from flask import jsonify
from flask import Flask
from flask import render_template
from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from utilities.constants import LOGGER_NAME_FRONTEND

from utilities.logger import Logger

from utilities.constants import APIKEY
from utilities.constants import KEY_JOB_TYPE
from utilities.constants import BASE64IMAGE
from utilities.constants import REFERENCE_IMG
from utilities.constants import MASK_IMG
from utilities.constants import MAX_JOB_NUMBER
from utilities.constants import OPTIONAL_KEYS
from utilities.constants import KEY_LANGUAGE
from utilities.constants import SUPPORTED_LANGS
from utilities.constants import REQUIRED_KEYS
from utilities.constants import UUID
from utilities.constants import VALUE_JOB_TXT2IMG
from utilities.constants import VALUE_JOB_IMG2IMG
from utilities.constants import VALUE_JOB_INPAINTING
from utilities.constants import VALUE_JOB_RESTORATION
from utilities.constants import IMAGE_NOT_FOUND_BASE64
from utilities.database import Database
from utilities.images import load_image

logger = Logger(name=LOGGER_NAME_FRONTEND)
database = Database(logger)
app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
)


@app.route("/add_job", methods=["POST"])
@limiter.limit("1/second")
def add_job():
    req = request.get_json()

    if APIKEY not in req:
        logger.error(f"{APIKEY} not present in {req}")
        return "", 401
    user = database.validate_user(req[APIKEY])
    if not user:
        logger.error(f"user not found with {req[APIKEY]}")
        return "", 401

    for key in req.keys():
        if (key not in REQUIRED_KEYS) and (key not in OPTIONAL_KEYS):
            return jsonify({"msg": "provided one or more unrecognized keys"}), 404

    # only checks required key for non-restoration jobs
    if req.get(KEY_JOB_TYPE, None) != VALUE_JOB_RESTORATION:
        for required_key in REQUIRED_KEYS:
            if required_key not in req:
                return jsonify({"msg": "missing one or more required keys"}), 404

    if (
        req[KEY_JOB_TYPE]
        in [VALUE_JOB_IMG2IMG, VALUE_JOB_INPAINTING, VALUE_JOB_RESTORATION]
        and REFERENCE_IMG not in req
    ):
        return jsonify({"msg": "missing reference image"}), 404

    if req[KEY_JOB_TYPE] == VALUE_JOB_INPAINTING and MASK_IMG not in req:
        return jsonify({"msg": "missing mask image"}), 404

    if KEY_LANGUAGE in req and req[KEY_LANGUAGE] not in SUPPORTED_LANGS:
        return jsonify({"msg": f"not suporting {req[KEY_LANGUAGE]}"}), 404

    if database.count_all_pending_jobs(req[APIKEY]) > MAX_JOB_NUMBER:
        return (
            jsonify({"msg": "too many jobs in queue, please wait or cancel some"}),
            500,
        )

    job_uuid = str(uuid.uuid4())
    logger.info("adding a new job with uuid {}..".format(job_uuid))

    database.insert_new_job(req, job_uuid=job_uuid)

    return jsonify({"msg": "", UUID: job_uuid})


@app.route("/cancel_job", methods=["POST"])
@limiter.limit("1/second")
def cancel_job():
    req = request.get_json()
    if APIKEY not in req:
        return "", 401
    user = database.validate_user(req[APIKEY])
    if not user:
        return "", 401

    if UUID not in req:
        return jsonify({"msg": "missing uuid"}), 404

    logger.info("cancelling job with uuid {}..".format(req[UUID]))

    result = database.cancel_job(job_uuid=req[UUID], apikey=req[APIKEY])

    if result:
        msg = "your job with uuid {} removed".format(req[UUID])
        return jsonify({"msg": msg})

    jobs = database.get_jobs(job_uuid=req[UUID])

    if jobs:
        return (
            jsonify(
                {
                    "msg": "your job {} is not in pending state, unable to cancel".format(
                        req[UUID]
                    )
                }
            ),
            405,
        )

    return (
        jsonify({"msg": "unable to find your job with uuid {}".format(req[UUID])}),
        404,
    )


@app.route("/get_jobs", methods=["POST"])
@limiter.limit("1/second")
def get_jobs():
    req = request.get_json()
    if APIKEY not in req:
        return "", 401
    user = database.validate_user(req[APIKEY])
    if not user:
        return "", 401

    # define max number of jobs to fetch from db
    job_count_limit = 20

    if UUID in req:
        jobs = database.get_jobs(
            job_uuid=req[UUID],
            apikey=req[APIKEY],
            job_types=req[KEY_JOB_TYPE].split(",") if req.get(KEY_JOB_TYPE, "") else [],
            limit_count=job_count_limit,
        )
    else:
        jobs = database.get_jobs(
            apikey=req[APIKEY],
            job_types=req[KEY_JOB_TYPE].split(",") if req.get(KEY_JOB_TYPE, "") else [],
            limit_count=job_count_limit,
        )

    for job in jobs:
        # load image to job if has one
        for key in [BASE64IMAGE, REFERENCE_IMG, MASK_IMG]:
            if key in job and "base64" not in job[key]:
                data = load_image(job[key], to_base64=True)
                job[key] = data if data else IMAGE_NOT_FOUND_BASE64

    return jsonify({"jobs": jobs})


@app.route("/random_jobs", methods=["GET"])
@limiter.limit("1/second")
def random_jobs():
    # define max number of jobs to fetch from db
    job_count_limit = 20

    jobs = database.get_random_jobs(limit_count=job_count_limit)

    for job in jobs:
        # load image to job if has one
        for key in [BASE64IMAGE, REFERENCE_IMG, MASK_IMG]:
            if key in job and "base64" not in job[key]:
                data = load_image(job[key], to_base64=True)
                job[key] = data if data else IMAGE_NOT_FOUND_BASE64

    return jsonify({"jobs": jobs})


@app.route("/")
@limiter.limit("1/second")
def index():
    return render_template("index.html")


@app.route("/restoration")
@limiter.limit("1/second")
def restoration():
    return render_template("restoration.html")


def main(args):
    database.set_image_output_folder(args.image_output_folder)
    database.connect(args.db)

    app.config["TITLE"] = args.title
    app.run(host="0.0.0.0", port=args.port)

    database.safe_disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Add an argument to set the 'debug' flag
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    # Add an argument to set the path of the database file
    parser.add_argument(
        "--db", type=str, default="happysd.db", help="Path to SQLite database file"
    )

    # Add an argument to set the title of service
    parser.add_argument(
        "--title", type=str, default="Happy Diffusion", help="Title of the webpage"
    )

    # Add an argument to set the path of the database file
    parser.add_argument(
        "--image-output-folder",
        "-o",
        type=str,
        default="",
        help="Path to output images",
    )

    # Add an argument to set the port
    parser.add_argument(
        "--port",
        type=str,
        default="8888",
        help="Port to expose the service",
    )

    args = parser.parse_args()

    main(args)
