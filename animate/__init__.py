"""
create_gif.py

A command line tool to create GIFs of stacks of time series
from the Descartes Labs platform.

Author: Krishna Karra, Chris Davis
"""

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from animate.utils.animation import transform_scenes, make_gif
from animate.utils.parse_inputs import (
    check_output_file,
    check_latlon_geojson,
    check_products_bands_scales,
    check_datetimes,
    check_tile_parameters,
    check_cloud_fraction,
    check_fill_fraction,
    check_valid_fraction,
    check_raster_len,
    check_sat_id,
    check_solar_az_angle,
    check_solar_el_angle,
    check_sort_field,
    check_sort_order,
    check_flatten,
    check_processing_level,
    check_crs,
    check_rescale,
    check_outsize,
    check_aspect_ratio,
    check_coregister,
    check_outdir,
    check_colormap,
    check_fps,
    check_program,
    check_export,
    check_bbox,
    check_summary,
    check_websafe,
    check_verbose,
)
from animate.utils.platform import (
    determine_geocontext,
    find_scenes,
    query_scenes,
    export_scenes,
)
from animate.utils.filter import build_filters
from animate.utils.export import export_bbox, export_summary

import sys
import os
import datetime


def get_parsed_args():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        "output_file", type=str, help="Output (.gif/.mp4) file to create"
    )
    parser.add_argument("--latlon", type=float, 
                        nargs="+", 
                        help="Lat & lon (deg)", default=[35.687, -105.9378])
    parser.add_argument(
        "--products",
        type=str,
        nargs="+",
        help="Product ID(s) separated by space",
        default=["landsat:LC08:01:RT:TOAR"],
    )
    parser.add_argument(
        "--bands", type=str, nargs="+", help="Bands", default=["red", "green", "blue"]
    )
    parser.add_argument(
        "--scales",
        type=int,
        nargs="+",
        help="Specify min & max values per band",
        default=None,
    )
    parser.add_argument(
        "--start_datetime", type=str, help="Start datetime", default="2019-01-01"
    )
    parser.add_argument(
        "--end_datetime", type=str, help="End datetime", default="2019-04-01"
    )
    parser.add_argument("--resolution", type=float, help="Resolution", default=None)
    parser.add_argument("--tilesize", type=int, help="Tilesize", default=None)
    parser.add_argument("--pad", type=int, help="Padding", default=None)
    parser.add_argument(
        "--cloud_fraction",
        type=float,
        help="Cloud fraction to filter search (vendor provided)",
        default=None,
    )
    parser.add_argument(
        "--fill_fraction",
        type=float,
        help="Minimum scene fill fraction (vendor provided)",
        default=None,
    )
    parser.add_argument(
        "--valid_fraction",
        type=float,
        help="Fraction of valid pixels per scene",
        default=None,
    )
    parser.add_argument(
        "--raster_len",
        type=int,
        help="Number of scenes to rasterize at a time (cannot be >500)",
        default=0,
    )
    parser.add_argument(
        "--sat_id", type=str, help="Select satellite ID within product", default=None
    )
    parser.add_argument(
        "--solar_az_angle",
        type=float,
        nargs="+",
        help="Specify min and max solar azimuth angle",
        default=None,
    )
    parser.add_argument(
        "--solar_el_angle",
        type=float,
        nargs="+",
        help="Specify min and max solar elevation angle",
        default=None,
    )
    parser.add_argument(
        "--sort_field",
        type=str,
        help="Metadata field to use to sort scenes by",
        default="acquired",
    )
    parser.add_argument(
        "--sort_order",
        type=str,
        help="Sort order for scenes (asc or desc)",
        default="asc",
    )
    parser.add_argument(
        "--flatten",
        type=str,
        help="Flatten (second | minute | hour | day | month | year) in stack",
        default=None,
    )
    parser.add_argument(
        "--processing_level",
        type=str,
        help="Processing level (toa | surface)",
        default=None,
    )
    parser.add_argument(
        "--crs",
        type=str,
        help="Coordinate reference system (EPSG or proj4)",
        default=None,
    )
    parser.add_argument(
        "--rescale",
        type=float,
        nargs="+",
        help="Min and max percentiles for use in rescaling",
        default=[2.0, 98.0],
    )
    parser.add_argument(
        "--outsize", type=int, nargs="+", help="Output GIF image size", default=None
    )
    parser.add_argument(
        "--aspect_ratio", type=int, nargs="+", help="Output aspect ratio", default=None
    )
    parser.add_argument(
        "--coregister",
        help="Coregister image stack to first frame",
        action="store_true",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        help="Output directory to write to (default home)",
        default=None,
    )
    parser.add_argument(
        "--cmap", type=str, help="Colormap for grayscale images", default="gray"
    )
    parser.add_argument("--fps", type=int, help="Frames per second for GIF", default=1)
    parser.add_argument(
        "--program", type=str, help="Backend program for GIF creation", default="ffmpeg"
    )
    parser.add_argument(
        "--export", help="Export each frame to geotiff", action="store_true"
    )
    parser.add_argument(
        "--bbox",
        help="Export bounding box of animation as GeoJSON",
        action="store_true",
    )
    parser.add_argument(
        "--summary",
        help="Export summary of animation to text file",
        action="store_true",
    )
    parser.add_argument(
        "--websafe", help="Make the video websafe using ffmpeg", action="store_true"
    )
    parser.add_argument(
        "--verbose", help="Enable verbose output to terminal", action="store_true"
    )
    parser.add_argument(
        "--geojson", help="Use a geojson to define the region", default=None
    )

    return parser.parse_args()


def main():
    args = get_parsed_args()

    # error check and grab all parameters
    output_file = check_output_file(args.output_file)

    resolution, tilesize, pad = check_tile_parameters(
        args.resolution, args.tilesize, args.pad
    )

    latlon, geojson = check_latlon_geojson(
        args.latlon, args.geojson, resolution, tilesize, pad
    )
    if latlon:
        print(datetime.datetime.now(), "Using lat lon of {0} {1}".format(latlon[0], latlon[1]))
    if geojson:
        print(datetime.datetime.now(), "Using geojson shape of {0}".format(geojson))

    products, bands_gif, bands_exp, scales = check_products_bands_scales(
        args.products, args.bands, args.scales
    )

    start, end = check_datetimes(args.start_datetime, args.end_datetime)

    cloud_fraction = check_cloud_fraction(args.cloud_fraction)
    fill_fraction = check_fill_fraction(args.fill_fraction)
    valid_fraction = check_valid_fraction(args.valid_fraction, args.bands)
    raster_len = check_raster_len(args.raster_len)
    sat_id = check_sat_id(args.sat_id)
    solar_az_angle = check_solar_az_angle(args.solar_az_angle)
    solar_el_angle = check_solar_el_angle(args.solar_el_angle)
    sort_field = check_sort_field(args.sort_field)
    sort_order = check_sort_order(args.sort_order)
    flatten = check_flatten(args.flatten)
    processing_level = check_processing_level(args.processing_level)
    crs = check_crs(args.crs)
    rescale = check_rescale(args.rescale)
    outsize = check_outsize(args.outsize)
    aspect_ratio = check_aspect_ratio(args.aspect_ratio)
    coregister = check_coregister(args.coregister)
    outdir = check_outdir(args.outdir)
    cmap = check_colormap(args.cmap)
    fps = check_fps(args.fps)
    program = check_program(args.program)
    export = check_export(args.export)
    bbox = check_bbox(args.bbox)
    summary = check_summary(args.summary)
    websafe = check_websafe(args.websafe)
    verbose = check_verbose(args.verbose)

    if verbose:
        print(datetime.datetime.now(), "Building metadata filters...")

    filters = build_filters(fill_fraction, sat_id, solar_az_angle, solar_el_angle)

    if verbose:
        print(datetime.datetime.now(), "Creating geocontext...")

    ctx = determine_geocontext(latlon, resolution, tilesize, pad, geojson, crs, verbose)

    if verbose:
        print(datetime.datetime.now(), "Finding scenes...")

    scenes, ctx = find_scenes(
        ctx,
        products,
        start,
        end,
        cloud_fraction,
        filters,
        sort_field,
        sort_order,
        verbose,
    )

    if len(scenes) == 0:
        print(
            datetime.datetime.now(),
            "Found no scenes with specified options! Exiting...",
        )
        sys.exit()

    if verbose:
        print(datetime.datetime.now(), "Querying scenes from platform...")

    img_stack, scenes_grouped = query_scenes(
        scenes,
        ctx,
        bands_gif,
        scales,
        processing_level,
        valid_fraction,
        raster_len,
        flatten,
        verbose,
    )

    if verbose:
        print(
            datetime.datetime.now(),
            "Applying transformations to {0} scenes...".format(len(scenes_grouped)),
        )

    frames = transform_scenes(
        img_stack, rescale, cmap, aspect_ratio, outsize, coregister
    )

    if verbose:
        print(datetime.datetime.now(), "Creating animation from processed scenes...")

    fname = os.path.join(outdir, output_file)
    make_gif(frames, fname, fps, program, websafe)

    if export:
        if verbose:
            print(datetime.datetime.now(), "Exporting each grouped scene to GeoTIFF...")
        export_dir = os.path.join(outdir, output_file[:-4])

        if not os.path.exists(export_dir):
            if verbose:
                print(
                    datetime.datetime.now(),
                    "Creating output directory {}".format(export_dir),
                )
            os.makedirs(export_dir)

        export_scenes(
            scenes_grouped,
            ctx,
            bands_exp,
            scales,
            processing_level,
            flatten,
            raster_len,
            export_dir,
            verbose,
        )

    if bbox:
        if verbose:
            print(datetime.datetime.now(), "Exporting bounding box to GeoJSON...")
        bbox_file = os.path.join(outdir, output_file[:-4] + ".geojson")
        export_bbox(ctx, bbox_file)

    if summary:
        if verbose:
            print(
                datetime.datetime.now(),
                "Exporting summary of animation to text file...",
            )
        txt_file = os.path.join(outdir, output_file[:-4] + ".txt")
        export_summary(scenes, ctx, txt_file)

    if verbose:
        print(
            datetime.datetime.now(), "\n* * Complete! Descartes Labs loves you <3 * *\n"
        )


if __name__ == "__main__":
    main()
