"""
animation.py

Utilities to create animations from imagery.

Author: Krishna Karra
"""

# define imports
import moviepy.editor as mpy
import numpy as np
from subprocess import check_output

from animate.utils.img_proc import rescale_img, crop_img, resize_img
from animate.utils.coregister import coregister_stack


def make_websafe(fname):
    fname_ext = fname[-4:]
    fname_websafe = fname.strip(fname_ext) + "_websafe" + fname_ext

    cmd = """ffmpeg -an -i {} -vcodec libx264 -pix_fmt yuv420p 
             -profile:v baseline -level 3 
             -vf pad=ceil(iw/2)*2:ceil(ih/2)*2 {}""".format(
        fname, fname_websafe
    )

    try:
        check_output(cmd.split())
    except:
        print(cmd)
        raise OSError("Failed to make websafe video!")


def transform_scenes(img_stack, rescale, cmap, aspect_ratio, outsize, coregister):
    """
    Transform a set of scenes 

    Parameters
    ----------
    img_stack: np.array
        Image stack as 4D NumPy array (index, X, Y, channels)
    rescale: list of floats
        List of [min, max] percentiles for rescaling
    cmap: matplotlib.colors.Colormap
        Colormap object that transforms a numpy array
    aspect_ratio: list
        Aspect ratio [width, height] to crop to
    outsize: tuple or list
        Resizes scenes to this size
    coregister: bool
        Flag to coregister image stack to eliminate pixel jitter

    Returns
    -------
    frames: list
        List of transformed NumPy arrays
    """

    xform_stack = list()
    pmin, pmax = rescale[0], rescale[1]

    # coregister stack to first frame
    if coregister:
        img_stack, shifts = coregister_stack(img_stack)

    do_crop = False
    if aspect_ratio:
        # TODO: check that this is right:
        # pil is [width, height] but numpy is [height, width]
        new_ratio = float(aspect_ratio[1]) / float(aspect_ratio[0])
        old_ratio = img_stack.shape[1] / img_stack.shape[2]
        if old_ratio != new_ratio:
            do_crop = True

    do_outsize = False
    if outsize:
        # TODO: check that this is right:
        # pil is [width, height] but numpy is [height, width]
        old_size = (img_stack.shape[2], img_stack.shape[1])
        if outsize[0] != old_size[0] or outsize[1] != old_size[1]:
            do_outsize = True

    for idx, img in enumerate(img_stack):
        # convert to floating point, between 0->1
        tmp_img = rescale_img(img, pmin=pmin, pmax=pmax)

        # apply colormap if grayscale
        if img.shape[-1] == 1:
            tmp_img = cmap(tmp_img.squeeze())[:, :, :-1]

        # rescale back to 0->255, Byte
        # we've already rescaled by percentile, so we're simply doing a type conversion here
        tmp_img = rescale_img(tmp_img, min_val=0, max_val=255, dtype=np.uint8)

        if do_crop:
            tmp_img = crop_img(tmp_img, aspect_ratio)
        if do_outsize:
            tmp_img = resize_img(tmp_img, outsize)

        xform_stack.append(tmp_img)

    return xform_stack


def make_gif(frames, fname, fps, program, websafe):
    """
    Write out a GIF from a stack of frames

    Parameters
    ----------
    frames: list
        List of NumPy arrays to animate
    fname: str
        Output filename (.gif/.mp4)
    fps: int
        Frames per second for animation
    program: str
        Backend program for animation generation
    websafe: bool
        Create a websafe version of animation

    Raises
    ------
    RuntimeError
        Fail to create animation

    """

    # create animation
    try:
        clip = mpy.ImageSequenceClip(frames, fps=fps)
        clip.write_gif(fname, fps=fps, program=program)
    except:
        raise RuntimeError("Animation creation failed! This is not good.")

    if websafe:
        make_websafe(fname)
