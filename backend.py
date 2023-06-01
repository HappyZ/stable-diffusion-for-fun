import argparse
import torch

from utilities.constants import LOGGER_NAME_BACKEND
from utilities.constants import LOGGER_NAME_TXT2IMG
from utilities.constants import LOGGER_NAME_IMG2IMG
from utilities.constants import LOGGER_NAME_INPAINT

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
from utilities.constants import VALUE_JOB_INPAINTING
from utilities.constants import VALUE_JOB_RESTORATION
from utilities.constants import REFERENCE_IMG
from utilities.constants import MASK_IMG

from utilities.translator import translate_prompt
from utilities.config import Config
from utilities.database import Database
from utilities.logger import Logger
from utilities.model import Model
from utilities.text2img import Text2Img
from utilities.img2img import Img2Img
from utilities.inpainting import Inpainting
from utilities.times import wait_for_seconds
from utilities.memory import empty_memory_cache
from utilities.external import gfpgan


logger = Logger(name=LOGGER_NAME_BACKEND)
database = Database(logger)


def load_model(
    logger: Logger, use_gpu: bool, gpu_device_name: str, reduce_memory_usage: bool
) -> Model:
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

    model = Model(
        model_name,
        inpainting_model_name,
        logger,
        use_gpu=use_gpu,
        gpu_device_name=gpu_device_name,
    )
    if use_gpu and reduce_memory_usage:
        model.set_low_memory_mode()
    model.load_all()

    return model


def backend(model, gfpgan_folderpath, is_debugging: bool):
    text2img = Text2Img(model, logger=Logger(name=LOGGER_NAME_TXT2IMG))
    text2img.breakfast()
    img2img = Img2Img(model, logger=Logger(name=LOGGER_NAME_IMG2IMG))
    img2img.breakfast()
    inpainting = Inpainting(model, logger=Logger(name=LOGGER_NAME_INPAINT))
    inpainting.breakfast()

    while 1:
        wait_for_seconds(1)

        if is_debugging:
            pending_jobs = database.get_jobs()
        else:
            pending_jobs = database.get_one_pending_job()
        if len(pending_jobs) == 0:
            continue

        next_job = pending_jobs[0]

        if not is_debugging:
            database.update_job(
                {KEY_JOB_STATUS: VALUE_JOB_RUNNING}, job_uuid=next_job[UUID]
            )

        prompt = next_job.get(KEY_PROMPT, "")
        negative_prompt = next_job.get(KEY_NEG_PROMPT, "")

        if (
            next_job[KEY_JOB_TYPE]
            in [VALUE_JOB_IMG2IMG, VALUE_JOB_INPAINTING, VALUE_JOB_TXT2IMG]
            and KEY_LANGUAGE in next_job
        ):
            if VALUE_LANGUAGE_EN != next_job[KEY_LANGUAGE]:
                logger.info(
                    f"found {next_job[KEY_LANGUAGE]}, translate prompt and negative prompt first"
                )
                prompt_en = translate_prompt(prompt, next_job[KEY_LANGUAGE])
                logger.info(f"translated {prompt} to {prompt_en}")
                prompt = prompt_en
                if negative_prompt:
                    negative_prompt_en = translate_prompt(
                        negative_prompt, next_job[KEY_LANGUAGE]
                    )
                    logger.info(f"translated {negative_prompt} to {negative_prompt_en}")
                    negative_prompt = negative_prompt_en

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
            elif next_job[KEY_JOB_TYPE] == VALUE_JOB_INPAINTING:
                ref_img = next_job[REFERENCE_IMG]
                mask_img = next_job[MASK_IMG]
                result_dict = inpainting.lunch(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    reference_image=ref_img,
                    mask_image=mask_img,
                    config=config,
                )
            elif next_job[KEY_JOB_TYPE] == VALUE_JOB_RESTORATION:
                ref_img_filepath = next_job[REFERENCE_IMG]
                result_dict = gfpgan(
                    gfpgan_folderpath,
                    next_job[UUID],
                    ref_img_filepath,
                    config=config,
                    logger=logger,
                )
                if not result_dict:
                    raise ValueError("failed to run gfpgan")
            else:
                raise ValueError("unrecognized job type")
        except KeyboardInterrupt:
            break
        except BaseException as e:
            logger.error(e)
            database.update_job(
                {KEY_JOB_STATUS: VALUE_JOB_FAILED}, job_uuid=next_job[UUID]
            )
            empty_memory_cache()
            continue

        database.update_job(result_dict, job_uuid=next_job[UUID])
        if not is_debugging:
            database.update_job(
                {KEY_JOB_STATUS: VALUE_JOB_DONE}, job_uuid=next_job[UUID]
            )

    logger.critical("stopped")


def main(args):
    database.set_image_output_folder(args.image_output_folder)
    database.connect(args.db)

    model = load_model(logger, args.gpu, args.gpu_device, args.reduce_memory_usage)
    backend(model, args.gfpgan, args.debug)

    database.safe_disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Add an argument to set the 'debug' flag
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    # Add an argument to set the path of the database file
    parser.add_argument(
        "--db", type=str, default="happysd.db", help="Path to SQLite database file"
    )

    # Add an argument to set the 'gpu' flag
    parser.add_argument("--gpu", action="store_true", help="Enable to use GPU device")

    # Add an argument to set the gpu device name
    parser.add_argument(
        "--gpu-device", type=str, default="cuda", help="GPU device name"
    )

    # Add an argument to reduce memory usage
    parser.add_argument(
        "--reduce-memory-usage",
        action="store_true",
        help="Reduce memory usage when using GPU",
    )

    # Add an argument to reduce memory usage
    parser.add_argument(
        "--gfpgan",
        type=str,
        default="",
        help="GFPGAN folderpath",
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
