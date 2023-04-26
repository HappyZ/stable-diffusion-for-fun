import gc
import torch


def empty_memory():
    '''
    Performs garbage collection and empty cache in cuda device
    '''
    gc.collect()
    torch.cuda.empty_cache()
