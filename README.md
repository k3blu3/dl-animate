# Descartes Labs Animation Tool

A tool for creating animations of time-stacks of imagery from
the Descartes Labs platform.

## ffmpeg

You must have either ffmpeg (recommended) or ImageMagick installed on your
system in order for this tool to create animations. The animations are
created using a Python package called MoviePy, which can use either ImageMagick
or ffmpeg as backend programs. I've found ffmpeg to work the best.

See here to install ffmpeg, if you don't have it:

http://ffmpeg.org/download.html

On a Mac, if you have Homebrew, it's as simple as doing:

`brew install ffmpeg`

## Installation

1. Check this out
  * `git clone git@github.com:descarteslabs/animate; cd animate`
2. Create a virtualenv or conda environment, activate it (Python 3).
   You can alternatively install it to your base metal system Python.
  * `mkvirtualenv animate; workon animate`
  * `conda create -n animate; conda activate animate`
3. Install the package
  * `pip3 install .`

Note that this package depends on the Descartes Labs platform package.

## Usage

You can run the tool with the `--help` flag to get a sense of the various options.

  * `dl-animate --help`

This will display the inputs required, and various options that can be set.

### Required Inputs

* `output_file` : Name of output file to create (.gif/.mp4)

Currently, polygon shapes are not supported, but can be added if useful.

### Settings

* `--latlon` : 		Latitude and Longitude in degrees.
			Default: `--latlon 35.687 -105.9378`
* `--geojson` :		GeoJSON specifying shape to animate over.
			Can be a FeatureCollection, Feature, or Geometry.
			If it is a featurecollection, will run _only_ the first feature.
			Default: not set, resolves to None
* `--products` : 	List of Product IDs to pull from Descartes Labs Catalog.
			If more than one product is specified, then they will be aggregated together.
			Note that they must have the same bands, and will be resampled to the specified resolution. 
			Default: `--products landsat:LC08:01:RT:TOAR`
* `--bands` : 		Bands, separated by a space, to rasterize from product
			An `alpha` band is supported (add at end), and the data will be masked.
			If len(bands) > 3 (excluding alpha), only the first three will be aimated.
			You can export an arbitrary number of bands, however.
			Default: `--bands red green blue`
* `--scales` : 		Scales, separated by a space, for each band
			If specified, each band must have two entries (min, max)
			You must specify scales for each band, if you wish to set this
			Default: not set, resolves to None
* `--start_datetime` : 	Start date string in XX-XX-XXXX (year, month, day) format
			You can also specify as XX-XX-XXXXTXX:XX:XX (addition of hour, minute, second)
			Default: `--start_datetime 2019-01-01`
* `--end_datetime` : 	End date string in XX-XX-XXXX (year, month, day) for mat
			Default: `--end_datetime 2019-04-01`
* `--resolution` : 	Resolution to pull imagery at, in meters
			Default: not set, resolves to None
* `--tilesize` : 	Tilesize for the specified lat, lon in pixels
			Default: not set, resolves to None
* `--pad` : 		Padding for the specified lat, lon in pixels
			Default: not set, resolves to None
* `--cloud_fraction` : 	Cloud fraction to filter search by [0.0, 1.0]
			Default: not set, resolves to None
* `--fill_fraction` :   Fill fraction to filter search by [0.0, 1.0]
			Default: not set, resolves to None
* `--valid_fraction` :  Valid fraction to filter scenes by [0.0, 1.0]
			Note that this is computed from the alpha band.
			Default: not set, resolves to None
* `--raster_len` : 	Number of scenes to rasterize at a time, between 0 and 500
			Useful to set if you're doing large raster calls
			Default: `--raster_len 500`
* `--sat_id` :		Satellite ID string to select within product
			Default: not set, resolves to None
* `--solar_az_angle` : 	Set min and max solar azimuth angle, between 0 and 360 deg
			Default: not set, resolves to None
* `--solar_el_angle` :  Set min and max solar elevation angle, between 0 and 360 deg
			Default: not set, resolves to None
* `--sort_field` :	Metadata field to sort scenes by
			Default: `--sort_field acquired`
* `--sort_order` :	Order (asc or desc) for scene sorting
			Default: `--sort_order asc`
* `--flatten` : 	Rule to flatten by during rasterization
			Options: year, month, day, hour, minute, second
			Default: not set, resolves to None
* `--processing_level`: Set processing level of product (toa, surface)
			Default: not set, resolves to None
* `--crs` :		Coordinate reference system as EPSG code or proj4 string
			Default: not set, resolves to None
* `--rescale` : 	Set [pmin, pmax] percentiles for rescaling every scene
			Default: [2, 98]
			This can be helpful for bringing out more colors from scenes
* `--outsize` : 	Desired output size (X, Y) of animation. 
			Default: not set, resolves to None
* `--aspect_ratio` : 	Desired aspect ratio of output animation, two entries, [width height]
			Default: not set, resolves to None (square)
* `--coregister` : 	Coregister image stack to reduce jitter
			Default: not set, resolves to False
* `--outdir` : 		Output directory to write animations to
			Default: home directory (~)
* `--cmap` : 		Colormap for grayscale images
			Default: `--cmap gray`
* `--fps` : 		Frames per second for animation
			Default: `--fps 1`
* `--program` : 	Backend program for GIF/MP4 creation (options: ffmpeg, ImageMagick)
			Default: `--program ffmpeg`
* `--export` : 		Export raw image stack as set of GeoTIFFs
			A folder will be created with the name of the output animation
			Each GeoTIFF will have a filename corresponding to the image ID
			Default: not set, resolves to False
* `--bbox` :		Export bounding box for animation to GeoJSON
			A file with the same name as the animation (but .geojson) will be created
			Default: not set, resolves to False
* `--summary` :		Export summary of animationm to a text file
			A file with the same name as the animation (but .txt) will be created
			Default: not set, resolves to False
* `--websafe` :		Convert an mp4 animation from ffmpeg to a websafe version (needs FFmpeg)
			Default: not set, resolves to False
* `--verbose` :		Enable verbose output to terminal
			Default: not set, resolves to False
## Tips and Tricks

1) Make sure your resolution, tilesize & pad are reasonable for your given product.
2) Make sure your date ranges are reasonable, or there will be too many scenes to process.
3) If you just want a bigger image (e.g. upsampled) and don't necessarily need all the 
   resolution, consider using `--outsize`.

## Feature Requests

Please file an issue on GitHub, and I'll get to it when I can!

## Examples

Landsat-8 RGB animation over Descartes Labs HQ in Santa Fe, from October 2018 - Apr 2019

`dl-animate DL_HQ_landsat8.gif --lat 35.688389 --lon -105.943495 --resolution 15.0 --tilesize 256 --pad 256 --cloud_fraction 0.5 --flatten day --verbose --start_datetime 2018-10-01 --end_datetime 2019-04-01 --fps 2`

Sentinel-2 IR animation over Decartes Labs Los Alamos office, from October 2018 - Apr 2019

`dl-animate DL_LA_sentinel2_IR.gif --lat 35.879881 --lon -106.300535 --products sentinel-2:L1C --bands swir2 swir1 nir alpha --resolution 10.0 --tilesize 512 --pad 256 --cloud_fraction 0.5 --flatten day --verbose --start_datetime 2018-10-01 --end_datetime 2020-04-01 --fps 2`
