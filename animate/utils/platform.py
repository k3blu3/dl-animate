"""
platform.py

Handy functions that wrap the Descartes Labs platform.

Author: Krishna Karra
"""

import descarteslabs as dl
import numpy as np
import datetime
import os

from descarteslabs.scenes.scene import Scene
from descarteslabs.scenes.scenecollection import SceneCollection


def determine_geocontext(latlon, resolution, tilesize, pad, geojson, crs, verbose):
    """
    Parameters
    ----------
    latlon: tuple or None
        Latitude/Longitude  in degrees
    resolution: float
        Resolution of data in meters
    tilesize: int
        Tilesize in pixels
    pad: int
        Padding in pixels
    geojson: dictionary
        Dictionary of features. Will _only_ take the first feature.
    crs: string
        Coordinate reference system (EPSG or proj4)
    verbose: bool
        Verbose output to terminal

    Returns
    -------
    Fully specified geocontext object
    """
    if geojson:
        if resolution is not None:
            ctx = dl.scenes.geocontext.AOI(geometry=geojson, resolution=resolution, crs=crs)
        else:
            shape = tilesize + 2 * pad
            ctx = dl.scenes.geocontext.AOI(geometry=geojson, shape=(shape, shape), crs=-crs)
    else:
        tile = dl.scenes.geocontext.DLTile.from_latlon(
            lat=latlon[0], lon=latlon[1], resolution=resolution, tilesize=tilesize, pad=pad
        )

        # shape encoded in tile geometry, so just feed in resolution
        ctx = dl.scenes.geocontext.AOI(geometry=tile.geometry, resolution=resolution, crs=crs)

    if verbose:
        print(datetime.datetime.now(), "Created geocontext: {0}".format(str(ctx)))

    return ctx


def find_scenes(
    ctx,
    products,
    start_datetime,
    end_datetime,
    cloud_fraction,
    filters,
    sort_field,
    sort_order,
    verbose,
):
    """
    Find relevant scenes from a product on platform.
    Returns a list of grouped metadata IDs and the dltile.

    Parameters
    ----------
    ctx: DL Geocontext object
        Could be either an AOI or a DLTile
    product: list of strings
        List of product IDs on Descartes Labs platform
    start_datetime: datetime.datetime object
        Start datetime
    end_datetime: datetime.datetime object
        End datetime
    cloud_fraction: float
        Cloud fraction to filter scenes by
        This is handled separately from other filtering expressions
    filters: list of expressions
        List of valid filtering expressions to pass to scenes
    sort_field: str
        Metadata field to sort scenes by
    sort_order: str
        Order to sort scenes by
    verbose: bool
        Verbose output to terminal

    Returns
    -------
    scenes: SceneCollections
    """

    # search for metadata IDs
    sd = start_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    ed = end_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    scenes, ctx = dl.scenes.search(
        aoi=ctx,
        products=products,
        start_datetime=sd,
        end_datetime=ed,
        query=filters,
        sort_field=sort_field,
        sort_order=sort_order,
        limit=None,
        cloud_fraction=cloud_fraction,
    )
    if verbose:
        print(datetime.datetime.now(), "Found {0} scenes".format(len(scenes)))
        print(datetime.datetime.now(), "Returned geocontext {0}".format(str(ctx)))


    return scenes, ctx


def slow_mosaic(scenes, bands, raster_len=1, bands_axis=-1, **kwargs):
    """Given a set of scenes, locally mosaic"""
    if bands_axis != -1:
        raise ValueError("expect bands_axis to be -1, got {0}".format(bands_axis))
    mosaic = None
    for sidx in range(0, len(scenes), raster_len):
        eidx = sidx + raster_len
        mosaic_i = scenes[sidx:eidx].mosaic(
            bands=bands, bands_axis=bands_axis, **kwargs
        )
        if mosaic is None:
            mosaic = mosaic_i
        else:
            # if we have a mask, use that
            if np.ma.is_masked(mosaic_i):
                mosaic[~mosaic_i.mask] = mosaic_i[~mosaic_i.mask]
                # if old or new mosaic pixel is unmasked
                # then resultant pixel is also unmasked:
                mosaic.mask = mosaic.mask * mosaic_i.mask
            elif "alpha" in bands:
                mask_indx = bands.index("alpha")
                mask = mosaic_i[..., mask_indx]
                for b in range(len(bands)):
                    mosaic[..., b][mask] = mosaic_i[..., b][mask]
            else:
                for b in range(len(bands)):
                    mosaic[:, :, b] = mosaic_i[:, :, b]

    return mosaic


def query_scenes(
    scenes,
    ctx,
    bands,
    scales,
    processing_level,
    valid_fraction,
    raster_len,
    flatten,
    verbose,
):
    """
    Query a set of scenes from a product on platform.
    Returns a list of image frames

    Parameters
    ----------
    scenes: SceneCollection
        Scenes we will pull stack of
    ctx: geocontext
    bands: list of strings
        Bands in product you wish to pull
    scales: list of tuples
        (src_min, src_max) tuple per band
    processing_level: str
        select processing level (toa | surface)
    valid_fraction: float
        valid fraction of pixels per scene to filter by
        uses the alpha band
    raster_len: int
        Number of ID groups to raster in a single call
    flatten: list of str
        Select flatten-by option to group scenes during rasterization
    verbose: bool
        Indicating verbose output to terminal

    Raises
    ------
    RuntimeError
        If Raster call fails

    Returns
    -------
    img_stack: np.array
        Stack of images as NumPy arrays  (index, X, Y, channels)
    """

    if verbose:
        print(
            datetime.datetime.now(), "Found {} scenes for timestack".format(len(scenes))
        )
        if flatten:
            print(datetime.datetime.now(), "Flattening over {0}".format(flatten))

    # if we set scales, make sure we set the output data type
    if scales:
        data_type = "Byte"
    else:
        data_type = "UInt16"

    # stack
    if raster_len:
        img_stack = []
        if flatten:
            # mosaic each flattened step
            for key, ss in scenes.groupby(*flatten):
                img_stack_i = slow_mosaic(
                    ss,
                    raster_len=raster_len,
                    bands=bands,
                    ctx=ctx,
                    scaling=scales,
                    bands_axis=-1,
                    processing_level=processing_level,
                    data_type=data_type,
                )
                img_stack.append(img_stack_i)

        else:
            for sidx in range(0, len(scenes), raster_len):
                eidx = sidx + raster_len
                img_stack_i = scenes[sidx:eidx].stack(
                    bands=bands,
                    ctx=ctx,
                    scaling=scales,
                    bands_axis=-1,
                    processing_level=processing_level,
                    data_type=data_type,
                )
                for img in img_stack_i:
                    img_stack.append(img)

        if np.ma.is_masked(img_stack):
            img_stack = np.ma.array(img_stack)
        else:
            img_stack = np.array(img_stack)
    else:
        img_stack = scenes.stack(
            bands=bands,
            ctx=ctx,
            flatten=flatten,
            scaling=scales,
            bands_axis=-1,
            processing_level=processing_level,
            data_type=data_type,
        )

    # grab grouped scenes
    scenes_grouped = list()
    if flatten:
        for key, ss in scenes.groupby(*flatten):
            scenes_grouped.append(ss)
    else:
        for ss in scenes:
            scenes_grouped.append(ss)

    # valid fraction filtering
    if valid_fraction:
        idxs_keep = list()
        num_pixels_per_img = img_stack.shape[1] * img_stack.shape[2]

        for idx, img in enumerate(img_stack):
            num_pixels_invalid = np.count_nonzero(img.mask[:, :, 0])
            valid_ratio = 1.0 - float(num_pixels_invalid) / float(num_pixels_per_img)
            if valid_ratio >= valid_fraction:
                idxs_keep.append(idx)

        img_stack = img_stack[idxs_keep, :, :, :]
        scenes_grouped = [scenes_grouped[idx] for idx in idxs_keep]
    
    if "alpha" in bands:
        img_stack = img_stack[:, :, :, :-1]

    # TODO: do we need to ensure this is not a masked array?

    return img_stack, scenes_grouped


def export_scenes(
    scenes, ctx, bands, scales, processing_level, flatten, raster_len, outdir, verbose
):
    """
    Export a set of scenes to individual GeoTIFFs.
    Note that these are "raw", no additional transformations are applied.

    Parameters
    ----------
    scenes: list of scene collections
        Scenes we will pull stack of
    ctx: geocontext
    bands: list of strings
        Bands in product you wish to pull
    scales: list of tuples
        (src_min, src_max) tuple per band
    processing_level: str
        select processing level (toa | surface)
    outdir: str
        Directory name to write GeoTIFF files
    verbose: bool
        Indicating verbose output to terminal

    Raises
    ------
    RuntimeError
        If Raster call fails for an ID group
    """

    # if we set scales, make sure we set the output data type
    if scales:
        data_type = "Byte"
    else:
        data_type = None

    for ss in scenes:
        if type(ss) == Scene:
            dest = os.path.join(outdir, ss.properties.id + '.tif')
            ss.download(bands=bands,
                        ctx=ctx,
                        dest=dest,
                        processing_level=processing_level,
                        scaling=scales,
                        data_type=data_type)
        elif type(ss) == SceneCollection:
            dest = os.path.join(outdir, ss[-1].properties.id + '.tif')
            ss.download_mosaic(bands=bands,
                               ctx=ctx,
                               dest=dest,
                               processing_level=processing_level,
                               scaling=scales,
                               data_type=data_type)

        if verbose:
            print(datetime.datetime.now(), 'Wrote GeoTIFF {}'.format(dest))
