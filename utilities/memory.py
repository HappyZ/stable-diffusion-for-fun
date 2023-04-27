import gc
import torch


def empty_memory():
    """
    Performs garbage collection and empty cache in cuda device.
    """
    gc.collect()
    torch.cuda.empty_cache()


def tune_for_low_memory():
    """
    Tunes PyTorch to use float16 to reduce memory footprint.
    """
    torch.set_default_dtype(torch.float16)
