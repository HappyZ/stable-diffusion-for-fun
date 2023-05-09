import argparse
import uuid
from flask import jsonify
from flask import Flask
from flask import render_template
from flask import request

from utilities.constants import LOGGER_NAME_FRONTEND

from utilities.logger import Logger

from utilities.constants import APIKEY
from utilities.constants import KEY_JOB_TYPE
from utilities.constants import REFERENCE_IMG
from utilities.constants import MAX_JOB_NUMBER
from utilities.constants import OPTIONAL_KEYS
from utilities.constants import KEY_LANGUAGE
from utilities.constants import SUPPORTED_LANGS
from utilities.constants import REQUIRED_KEYS
from utilities.constants import UUID
from utilities.constants import VALUE_JOB_TXT2IMG
from utilities.constants import VALUE_JOB_IMG2IMG
from utilities.constants import VALUE_JOB_INPAINTING
from utilities.database import Database

logger = Logger(name=LOGGER_NAME_FRONTEND)
database = Database(logger)
app = Flask(__name__)


@app.route("/add_job", methods=["POST"])
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
    for required_key in REQUIRED_KEYS:
        if required_key not in req:
            return jsonify({"msg": "missing one or more required keys"}), 404

    if req[KEY_JOB_TYPE] == VALUE_JOB_IMG2IMG and REFERENCE_IMG not in req:
        return jsonify({"msg": "missing reference image"}), 404

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

    result = database.cancel_job(job_uuid=req[UUID])

    if result:
        msg = "job with uuid {} removed".format(req[UUID])
        return jsonify({"msg": msg})

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
    user = database.validate_user(req[APIKEY])
    if not user:
        return "", 401

    jobs = database.get_jobs(job_uuid=req[UUID])

    return jsonify({"jobs": jobs})


@app.route("/")
def index():
    return render_template("index.html")


def main(args):
    database.set_image_output_folder(args.image_output_folder)
    database.connect(args.db)

    if args.debug:
        app.run(host="0.0.0.0", port="5432")
    else:
        app.run(host="0.0.0.0", port="8888")

    database.safe_disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Add an argument to set the 'debug' flag
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    # Add an argument to set the path of the database file
    parser.add_argument(
        "--db", type=str, default="happysd.db", help="Path to SQLite database file"
    )

    # Add an argument to set the path of the database file
    parser.add_argument(
        "--image-output-folder",
        "-o",
        type=str,
        default="",
        help="Path to output images",
    )

    args = parser.parse_args()

    main(args)
