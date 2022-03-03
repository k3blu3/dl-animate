"""
parse_inputs.py

Parse command line inputs, and return useful parameters.
"""

# define imports
from datetime import datetime
import os
import json
from warnings import warn

from matplotlib import pyplot as plt
import descarteslabs as dl


def check_output_file(output_file):
    try:
        assert output_file.endswith(".gif") or output_file.endswith(".mp4")
    except:
        raise ValueError("Output file must end in .gif or .mp4")

    return output_file


def check_latlon_geojson(latlon, geojson, resolution, tilesize, pad):
    if geojson:
        # either a resolution, or tilesize & pad should be specified
        check1 = resolution is not None
        check2 = (tilesize is not None) & (pad is not None)

        try:
            assert (check1 or check2) and not (check1 and check2)
        except:
            raise ValueError(
                "For geojson, either resolution OR tilesize & pad must be specified!"
            )

        print(
            "Processing geojson at {0} and ignoring lat/lon of {1} {2}".format(
                geojson, latlon[0], latlon[1]
            )
        )
        if geojson.endswith('json') or geojson.endswith('geojson'):
            with open(geojson, "r") as f:
                geojson_dict = json.load(f)
        else:
            geojson_dict = dl.places.shape(geojson)

        if "features" in geojson_dict:
            if len(geojson_dict["features"]) > 1:
                print(
                    "Warning! Found {0} features, but only taking first!".format(
                        len(geojson_dict["features"])
                    )
                )
            geojson = geojson_dict["features"][0]["geometry"]
        elif "geometry" in geojson_dict:
            geojson = geojson_dict["geometry"]
        else:
            geojson = geojson_dict
        latlon = None
    else:
        check = (resolution is not None) & (tilesize is not None) & (pad is not None)
        assert check

    if geojson is None and (latlon is None):
        raise ValueError("Need to either specify a geojson shape or else a lat and lon")
    return latlon, geojson


def check_products_bands_scales(products, bands, scales):
    for product in products:
        try:
            _ = dl.metadata.get_product(product)
        except:
            raise ValueError("Product {} not found!".format(product))

        try:
            product_bands_list = dl.metadata.bands(product)
            drv_bands_list = dl.metadata.derived_bands()

            product_bands = [b["name"] for b in product_bands_list]
            drv_bands = [b["name"] for b in drv_bands_list]

            avail_bands = product_bands + drv_bands

            assert set(bands).issubset(set(avail_bands))

            bands_gif = list()
            bands_exp = list()
            for bidx, b in enumerate(bands):
                bands_exp.append(b)
                if bidx < 3 or b == "alpha":
                    bands_gif.append(b)

        except:
            raise ValueError("Bands {} are not valid!".format(bands))

    try:
        if scales:
            assert len(scales) == 2 * len(bands)
            scales_format = list()
            for sidx in range(0, len(scales), 2):
                scales_format.append((scales[sidx], scales[sidx + 1]))
        else:
            scales_format = None
    except:
        raise ValueError(
            "Scales {} are invalid, you must specify per band".format(scales)
        )

    return products, bands_gif, bands_exp, scales_format


def check_datetimes(start_datetime, end_datetime):
    try:
        if "T" in start_datetime:
            start = datetime.strptime(start_datetime, "%Y-%m-%dT%H:%M:%S")
        else:
            start = datetime.strptime(start_datetime, "%Y-%m-%d")

        if "T" in end_datetime:
            end = datetime.strptime(end_datetime, "%Y-%m-%dT%H:%M:%S")
        else:
            end = datetime.strptime(end_datetime, "%Y-%m-%d")

    except:
        raise ValueError(
            "Failed to parse {} and {} datetimes!".format(start_datetime, end_datetime)
        )

    return start, end


def check_tile_parameters(resolution, tilesize, pad):
    try:
        if resolution is not None:
            assert resolution > 0.0
    except:
        raise ValueError("Resolution {} is invalid!".format(resolution))

    try:
        if tilesize is not None:
            assert tilesize > 0
    except:
        raise ValueError("Tilesize {} is invalid!".format(tilesize))

    try:
        if pad is not None:
            assert pad >= 0
    except:
        raise ValueError("Pad {} is invalid!".format(pad))

    return resolution, tilesize, pad


def check_cloud_fraction(cloud_fraction):
    if cloud_fraction:
        try:
            assert cloud_fraction <= 1.0 and cloud_fraction >= 0.0
        except:
            raise ValueError("Cloud fraction {} is invalid!".format(cloud_fraction))

    return cloud_fraction


def check_fill_fraction(fill_fraction):
    if fill_fraction:
        try:
            assert 0.0 <= fill_fraction <= 1.0
        except:
            raise ValueError("Fill fraction {} is invalid!".format(fill_fraction))

    return fill_fraction


def check_valid_fraction(valid_fraction, bands):
    try:
        assert valid_fraction is None or (
            valid_fraction <= 1.0 and valid_fraction >= 0.0
        )
        #if valid_fraction:
        #    if "alpha" not in bands:
        #        raise ValueError(
        #            "An alpha band must be provided if valid fraction is provided!"
        #        )
    except:
        raise ValueError("Valid fraction {} is invalid!".format(valid_fraction))

    return valid_fraction


def check_raster_len(raster_len):
    try:
        assert 0 <= raster_len <= 500
    except:
        raise ValueError(
            "Number of scenes to rasterize at a time must be between 0 and 500!"
        )

    return raster_len


def check_sat_id(sat_id):
    return sat_id


def check_solar_az_angle(solar_az_angle):
    if solar_az_angle:
        try:
            assert len(solar_az_angle) == 2
        except:
            raise ValueError("Solar azimuth angle must be length 2, [min, max]!")

        try:
            for a in solar_az_angle:
                assert 0.0 <= a <= 360.0
        except:
            raise ValueError("Solar azimuth angles must be between 0 and 360 deg!")

    return solar_az_angle


def check_solar_el_angle(solar_el_angle):
    if solar_el_angle:
        try:
            assert len(solar_el_angle) == 2
        except:
            raise ValueError("Solar elevation angle must be length 2, [min, max]!")

        try:
            for a in solar_el_angle:
                assert 0.0 <= a <= 360.0
        except:
            raise ValueError("Solar elevation angles must be between 0 and 360 deg!")

    return solar_el_angle


def check_sort_field(sort_field):
    return sort_field


def check_sort_order(sort_order):
    try:
        options = ["asc", "desc"]
        assert sort_order in options

    except:
        raise ValueError('Sort order must be either "asc" or "desc"!')

    return sort_order


def check_flatten(flatten):
    try:
        options = ["year", "month", "day", "hour", "minute", "second"]
        if flatten:
            assert flatten in options
        
            # need the properties.date
            flatten = [
            "properties.date." + i for i in options[: options.index(flatten) + 1]
            ]

    except:
        raise ValueError("Flatten {} is an invalid option!".format(flatten))

    return flatten


def check_processing_level(processing_level):
    try:
        options = ["toa", "surface"]
        if processing_level:
            assert processing_level in options

    except:
        raise ValueError("Processing level {} is an invalid option!".format(processing_level))

    return processing_level


def check_crs(crs):
    try:
        if crs:
            epsg_check = 'EPSG' in crs
            proj_check = 'proj' in crs
            assert(epsg_check or proj_check)
    except:
        raise ValueError('CRS {} must be an EPSG code or a proj4 string'.format(crs))

    return crs


def check_rescale(rescale):
    try:
        assert len(rescale) == 2
    except:
        raise ValueError("Rescale must be length 2, [pmin, pmax]")

    try:
        for r in rescale:
            assert 0.0 <= r <= 100.0
    except:
        raise ValueError("pmin and pmax must be between 0 and 100 (percentile)")

    return rescale


def check_outsize(outsize):
    try:
        assert outsize is None or len(outsize) == 2
    except:
        raise ValueError("Outsize must be a tuple or list of length 2 (X, Y)")

    return outsize


def check_aspect_ratio(aspect_ratio):
    try:
        if aspect_ratio:
            assert len(aspect_ratio) == 2
    except:
        raise ValueError("Aspect ratio {} is an invalid option!".format(aspect_ratio))

    return aspect_ratio


def check_coregister(coregister):
    return coregister


def check_outdir(outdir):
    try:
        if outdir:
            if not os.path.exists(outdir):
                warn("Output directory {} does not exist! Creating...".format(outdir))
                os.makedirs(outdir)

        else:
            # grab home directory
            outdir = os.path.expanduser("~")
    except:
        raise ValueError("Could not create output directory {}".format(outdir))

    return outdir


def check_colormap(cmap):
    try:
        cm = plt.get_cmap(cmap)
    except:
        raise ValueError("Could not retrieve colormap {}".format(cmap))

    return cm


def check_fps(fps):
    try:
        assert fps > 0 and fps <= 30
    except:
        raise ValueError("Frames per second for GIF/MP4 must be between 0 and 30")

    return fps


def check_program(program):
    try:
        options = ["imageio", "ImageMagick", "ffmpeg"]
        assert program in options
    except:
        raise ValueError("Program {} for GIF/MP4 creation is invalid".format(program))

    return program


def check_export(export):
    return export


def check_bbox(bbox):
    return bbox


def check_summary(summary):
    return summary


def check_websafe(websafe):
    return websafe


def check_verbose(verbose):
    return verbose
