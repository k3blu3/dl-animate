"""
coregister.py

Some simple scripts to coregister images.
Coregistration is done in the Fourier domain using pyfftw, scipy, and skimage

Shamelessly stolen from appsci_utils. Code is courtesy of Chris & Rick.

Author: Krishna Karra

"""

import numpy as np
import pyfftw
from skimage.feature import register_translation
import scipy.ndimage.fourier as snf


def coregister_stack(stack, base_frame=0, upsample=10, dtype=np.float32, do_shift=True):
    """
    Simple phase-correlation stack coregisterer. Align your image relative
    to base_frame (default is the 0th image) by analyzing fourier transform.

    Parameters
    ----------
    stack : numpy array (frames, rows, cols, channels)
        Images to coregister.
    base_frame : int, optional
        Which frame to coregister to.
        Default is to coregister to the 0th image
    upsample : int, optional
        Upsampling factor. Images will be registered to within 1 /
        upsample_factor of a pixel. For example upsample_factor == 20 means the
        images will be registered within 1/20th of a pixel.
        Default is to 10.
    dtype : numpy dtype, optional
        Dtype used for computations.
        Default is float32
    do_shift : boolean, optional
        If True [the default], will also shift the stack based on the median
        shift of the bands.
        If False, will just return the shifts.

    Returns
    -------
    if `do_shift == True`:
        shifted_image : numpy array (frame, row, col, channel)
            The shifted image
        averaged_shifts : numpy array (frame, 2)
            The shift applied (median over channels).
    if `do_shift == False:`
        shifts : numpy array (frame, channel, 2)
            The measured shift by channel.
    """

    num_frames, num_rows, num_columns, num_channels = stack.shape

    # channel shifts will be computed separately, then averaged
    shifts = np.zeros((num_frames, num_channels, 2), dtype=dtype)

    # compute FFT of all frames and bands
    obj = pyfftw.empty_aligned(stack.shape, dtype=dtype)
    obj[:] = stack.astype(dtype)
    fft_stack = pyfftw.interfaces.numpy_fft.fft2(obj, axes=(1, 2))

    for frame in range(num_frames):
        if frame == base_frame:
            continue
        for layer in range(num_channels):
            shift = register_translation(
                fft_stack[base_frame, :, :, layer],
                fft_stack[frame, :, :, layer],
                upsample_factor=upsample,
                space="fourier",
            )[0]
            shifts[frame, layer] = shift

    if do_shift:
        # average shifts by channel
        averaged_shifts = np.median(shifts, axis=1)  # (num_frames, 2)
        # since we already have the FFT, use it to implement shift
        return shift_stack(fft_stack, averaged_shifts, space="fourier"), averaged_shifts
    else:
        return shifts


def shift_stack(stack, shifts, space="real", dtype=np.float32):
    """
    Given stack and associated shifts, shift image in fourier space

    Parameters
    ----------
    stack : numpy array (frames, rows, cols, channels)
        Images to coregister.
    shifts : numpy array (frames, 2)
        Direction to shift each frame. The same shift is applied ot each channel.
    space : string of either 'fourier' or 'real', optional
        Defines how the algorithm interprets input data. “real” means data will
        be FFT’d to compute the correlation, while “fourier” data will bypass
        FFT of input data. Case insensitive.
    dtype : numpy dtype, optional
        Dtype used for computations.
        Default is float32

    Returns
    -------
    shifted_image : numpy array (frame, row, col, channel)
        The shifted image
    """

    num_frames, num_rows, num_columns, num_channels = stack.shape

    # compute FFT of all frames and bands
    if space.lower() == "real":
        obj = pyfftw.empty_aligned(stack.shape, dtype=dtype)
        obj[:] = stack.astype(dtype)
        fft_stack = pyfftw.interfaces.numpy_fft.fft2(obj, axes=(1, 2))
    # unless we already did that
    elif space.lower() == "fourier":
        fft_stack = stack
    else:
        raise ValueError("Unrecognized shift space {0}".format(space))

    shifted_stack = np.empty_like(fft_stack, dtype=dtype)
    for frame in range(num_frames):
        shift = shifts[frame]
        for layer in range(num_channels):
            shifted_stack[frame, :, :, layer] = np.real(
                pyfftw.interfaces.numpy_fft.ifft2(
                    snf.fourier_shift(fft_stack[frame, :, :, layer], shift)
                )
            )

    return shifted_stack
