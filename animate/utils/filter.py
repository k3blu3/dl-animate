"""
filter.py

Useful filtering operations.

Author: Krishna Karra, Chris Davis
"""

import descarteslabs as dl


def build_filters(fill_fraction, sat_id, solar_az_angle, solar_el_angle):
    """
    Build a set of metadata filters

    Parameters
    ----------
    fill_fraction: float
        Fraction of valid / total pixels in scene
    sat_id: str
        Satellite ID
    solar_az_angle: list of floats
        [min, max] solar azimuth angle in degrees
    solar_el_angle: list of floats
        [min, max] solar elevation angle in degrees

    Returns
    -------
    filters: list
        List of filtering expressions that can be evaluated
    """

    filters = list()
    if fill_fraction:
        filters.append(dl.properties.fill_fraction >= "{}".format(fill_fraction))

    if sat_id:
        filters.append(dl.properties.sat_id == "{}".format(sat_id))

    if solar_az_angle:
        filters.append(
            "{}".format(solar_az_angle[0])
            <= dl.properties.solar_azimuth_angle
            <= "{}".format(solar_az_angle[1])
        )

    if solar_el_angle:
        filters.append(
            "{}".format(solar_el_angle[0])
            <= dl.properties.solar_elevation_angle
            <= "{}".format(solar_el_angle[1])
        )

    if not filters:
        filters = None
    else:
        f = filters[0]
        for fi in filters[1:]:
            f = f & fi
        filters = f

    return filters
