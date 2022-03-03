"""
img_proc.py

Image processing functions for transforming a stack of imagery.

Author: Krishna Karra
"""

import numpy as np
from PIL import Image


def resize_img(img, new_size):
    """
    Resize an image to any desired dimension.

    Parameters
    ----------
    img: np.array
        Image as NumPy array
    new_size: tuple or list
        Desired output size
        Note, this should typically only be for X and Y dimensions

    Returns
    -------
    img_resize: np.array
        Resized image as NumPy array
    """

    img_resize = np.array(Image.fromarray(img.squeeze()).resize(size=new_size))

    if len(img_resize.shape) == 2:
        img_resize = img_resize[..., np.newaxis]

    return img_resize


def crop_img(img, aspect_ratio):
    """
    Crop an image to a new aspect ratio.

    Parameters
    ----------
    img: np.array
        Image as NumPy array
    aspect_ratio: list
        Aspect ratio [width, height] to crop to

    Returns
    -------
    img_crop: np.array
        Cropped image as NumPy array
    """

    ratio = float(aspect_ratio[1]) / float(aspect_ratio[0])

    # compute start and end pixels for height
    old_height = img.shape[0]
    new_height = old_height * ratio

    start = round((old_height - new_height) / 2.0)
    end = round(start + new_height)

    img_crop = img[start:end, :, :]
    return img_crop


def rescale_img(img, min_val=0.0, max_val=1.0, dtype=np.float32, pmin=0.0, pmax=100.0):
    """
    Return a scaled image between [0, 255] regardless of input scaling.

    Parameters
    ----------
    img: np.array
        Image as NumPy array
    min_val: float
        Minimum value of rescaled image (default 0.0)
    max_val: float
        Maximum value of rescaled image (default 1.0)
    dtype : np.dtype
        Type to return rescaled image (default np.float32)
    pmin : float
        Minimum percentage of values for scaling (default 0%)
    pmax : float
        Maximum percentage of values for scaling (default 100%)

    Returns
    -------
    img_rescale: np.array
        Image as NumPy array

    """

    # compute min and max percentile ranges to scale with
    vmin, vmax = np.nanpercentile(img, pmin), np.nanpercentile(img, pmax)

    # rescale & clip
    img_rescale = ((img - vmin) * (1.0 / (vmax - vmin) * max_val)).astype(dtype)
    np.clip(img_rescale, min_val, max_val, out=img_rescale)

    return img_rescale
