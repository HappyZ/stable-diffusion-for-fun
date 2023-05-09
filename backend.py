import argparse

from utilities.constants import LOGGER_NAME_BACKEND
from utilities.constants import LOGGER_NAME_TXT2IMG
from utilities.constants import LOGGER_NAME_IMG2IMG

from utilities.constants import UUID
from utilities.constants import KEY_LANGUAGE
from utilities.constants import VALUE_LANGUAGE_EN
from utilities.constants import KEY_PROMPT
from utilities.constants import KEY_NEG_PROMPT
from utilities.constants import KEY_JOB_STATUS
from utilities.constants import VALUE_JOB_DONE
from utilities.constants import VALUE_JOB_FAILED
from utilities.constants import VALUE_JOB_RUNNING
from utilities.constants import KEY_JOB_TYPE
from utilities.constants import VALUE_JOB_TXT2IMG
from utilities.constants import VALUE_JOB_IMG2IMG
from utilities.constants import REFERENCE_IMG

from utilities.translator import translate_prompt
from utilities.config import Config
from utilities.database import Database
from utilities.logger import Logger
from utilities.model import Model
from utilities.text2img import Text2Img
from utilities.img2img import Img2Img
from utilities.times import wait_for_seconds


logger = Logger(name=LOGGER_NAME_BACKEND)
database = Database(logger)


def load_model(logger: Logger, use_gpu: bool) -> Model:
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
    model_name = "SG161222/Realistic_Vision_V2.0"
    # inpainting model candidates:
    # "runwayml/stable-diffusion-inpainting"
    inpainting_model_name = "runwayml/stable-diffusion-inpainting"

    model = Model(model_name, inpainting_model_name, logger, use_gpu=use_gpu)
    if use_gpu:
        model.set_low_memory_mode()
    model.load_all()

    return model


def backend(model, is_debugging: bool):
    text2img = Text2Img(model, logger=Logger(name=LOGGER_NAME_TXT2IMG))
    text2img.breakfast()
    img2img = Img2Img(model, logger=Logger(name=LOGGER_NAME_IMG2IMG))
    img2img.breakfast()

    while 1:
        wait_for_seconds(1)

        if is_debugging:
            pending_jobs = database.get_jobs()
        else:
            pending_jobs = database.get_all_pending_jobs()
        if len(pending_jobs) == 0:
            continue

        next_job = pending_jobs[0]

        if not is_debugging:
            database.update_job(
                {KEY_JOB_STATUS: VALUE_JOB_RUNNING}, job_uuid=next_job[UUID]
            )

        prompt = next_job[KEY_PROMPT]
        negative_prompt = next_job[KEY_NEG_PROMPT]

        if KEY_LANGUAGE in next_job:
            logger.info(
                f"found {next_job[KEY_LANGUAGE]}, translate prompt and negative prompt first"
            )
            if VALUE_LANGUAGE_EN != next_job[KEY_LANGUAGE]:
                prompt_en = translate_prompt(prompt, next_job[KEY_LANGUAGE])
                logger.info(f"translated {prompt} to {prompt_en}")
                prompt = prompt_en
                if negative_prompt:
                    negative_prompt_en = translate_prompt(
                        negative_prompt, next_job[KEY_LANGUAGE]
                    )
                    logger.info(f"translated {negative_prompt} to {negative_prompt_en}")
                    negative_prompt = negative_prompt_en

        prompt += "RAW photo, (high detailed skin:1.2), 8k uhd, dslr, high quality, film grain, Fujifilm XT3"
        negative_prompt += "(deformed iris, deformed pupils:1.4), worst quality, low quality, jpeg artifacts, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck"

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
        except KeyboardInterrupt:
            break
        except BaseException as e:
            logger.error("text2img.lunch error: {}".format(e))
            if not is_debugging:
                database.update_job(
                    {KEY_JOB_STATUS: VALUE_JOB_FAILED}, job_uuid=next_job[UUID]
                )
            continue

        if not is_debugging:
            database.update_job(
                {KEY_JOB_STATUS: VALUE_JOB_DONE}, job_uuid=next_job[UUID]
            )
        database.update_job(result_dict, job_uuid=next_job[UUID])

    logger.critical("stopped")


def main(args):
    database.connect(args.db)

    model = load_model(logger, args.gpu)
    backend(model, args.debug)

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
    parser.add_argument("--gpu", action="store_true", help="Enable to use GPU device")

    args = parser.parse_args()

    main(args)