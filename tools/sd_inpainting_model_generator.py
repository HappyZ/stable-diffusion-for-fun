import os
import requests
import argparse
import safetensors
import torch
import sys

# List of checkpoint dictionary keys to skip during merging
keys_to_skip_on_merge = [
    "cond_stage_model.transformer.text_model.embeddings.position_ids"
]

# Dictionary for replacing keys in checkpoint dictionary
key_replacements = {
    "cond_stage_model.transformer.embeddings.": "cond_stage_model.transformer.text_model.embeddings.",
    "cond_stage_model.transformer.encoder.": "cond_stage_model.transformer.text_model.encoder.",
    "cond_stage_model.transformer.final_layer_norm.": "cond_stage_model.transformer.text_model.final_layer_norm.",
}


def transform_checkpoint_key(key):
    for text, replacement in key_replacements.items():
        if key.startswith(text):
            key = replacement + key[len(text) :]
    return key


def get_state_dict_from_checkpoint(ckpt_dict):
    ckpt_dict = ckpt_dict.pop("state_dict", ckpt_dict)

    return {
        transform_checkpoint_key(k): v
        for k, v in ckpt_dict.items()
        if transform_checkpoint_key(k) is not None
    }


def download_model(url):
    filepath = f"/tmp/{os.path.basename(url)}"
    if os.path.isfile(filepath):
        return filepath

    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    block_size = 1048576  # 1 MB
    downloaded_size = 0

    with open(filepath, "wb") as file:
        for data in response.iter_content(block_size):
            downloaded_size += len(data)
            file.write(data)
            # Calculate the progress
            progress = downloaded_size / total_size * 100
            print(f"Download progress: {progress:.2f}%")
    return filepath


def load_model(checkpoint_file):
    if "http" in checkpoint_file:
        filepath = download_model(checkpoint_file)
    else:
        filepath = checkpoint_file
    if not filepath:
        raise ValueError(f"empty filepath for {checkpoint_file}")

    _, extension = os.path.splitext(filepath)
    if extension.lower() == ".safetensors":
        model = safetensors.torch.load_file(filepath, device="cpu")
    else:
        model = torch.load(filepath, map_location="cpu")

    return get_state_dict_from_checkpoint(model)


def generate(args):
    input_model = args.model
    inpainting_model_url = "https://huggingface.co/runwayml/stable-diffusion-inpainting/resolve/main/sd-v1-5-inpainting.ckpt"
    inpainting_model_name = os.path.basename(inpainting_model_url)
    base_model_url = "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned.ckpt"
    base_model_name = os.path.basename(base_model_url)
    output_model = f"{input_model.split('.')[0]}-inpainting.{input_model.split('.')[1]}"

    print(f"Loading {input_model}")
    input_state_dict = load_model(input_model)

    print(f"Loading {base_model_name}")
    base_state_dict = load_model(base_model_url)

    for key in input_state_dict.keys():
        if key in keys_to_skip_on_merge:
            continue

        if "model" in key:
            if key in base_state_dict:
                base_value = base_state_dict.get(
                    key, torch.zeros_like(input_state_dict[key])
                )
                input_state_dict[key] = input_state_dict[key] - base_value
            else:
                input_state_dict[key] = torch.zeros_like(input_state_dict[key])

    del base_state_dict

    print(f"Merging {inpainting_model_name} and the above difference")
    inpainting_state_dict = load_model(inpainting_model_url)
    for key in inpainting_state_dict.keys():
        if input_state_dict and "model" in key and key in input_state_dict:
            if key in keys_to_skip_on_merge:
                continue

            a = inpainting_state_dict[key]
            b = input_state_dict[key]

            if (
                a.shape != b.shape
                and a.shape[0:1] + a.shape[2:] == b.shape[0:1] + b.shape[2:]
            ):
                assert (
                    a.shape[1] == 9 and b.shape[1] == 4
                ), f"Bad dimensions for merged layer {key}: A={a.shape}, B={b.shape}"
                inpainting_state_dict[key][:, 0:4, :, :] = add_difference(
                    a[:, 0:4, :, :], b, 1
                )
                result_is_inpainting_model = True
            else:
                inpainting_state_dict[key] = add_difference(a, b, 1)

    del input_state_dict

    print("Saving the model")
    _, extension = os.path.splitext(output_model)
    if extension.lower() == ".safetensors":
        safetensors.torch.save_file(inpainting_state_dict, output_model)
    else:
        torch.save(inpainting_state_dict, output_model)


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=str)

    args = parser.parse_args()

    generate(args)


if __name__ == "__main__":
    main()
