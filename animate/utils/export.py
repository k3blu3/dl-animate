"""
export.py

Functions to export information to file.

Author: Krishna Karra
"""

import descarteslabs as dl

import json
from pprint import pformat


def export_summary(ids_group, dltile, outfile):
    """
    Export the summary of the animation to a text file

    Parameters
    ----------
    ids_group: list of lists
        List of grouped metadata IDs
    dltile: dict
        DLTile specifying geocontext
    outfile: string
        Output text file to write to

    Raises
    ------
    RuntimeError
        If export to summary fails
    """

    try:
        with open(outfile, "w") as f:
            # write out geometry
            f.write("---BOUNDING BOX---\n")
            dltile_pretty = pformat(dltile, indent=4, compact=True)
            f.write(dltile_pretty)
            f.write("\n\n")

            # write out metadata for each ID group
            f.write(
                "There are {} scene groups in this animation\n\n".format(len(ids_group))
            )
            for idx, id_group in enumerate(ids_group):
                f.write(
                    "---ID Group {}, with {} scenes---\n".format(idx, len(id_group))
                )
                for this_id in id_group:
                    meta = dl.metadata.get(this_id)
                    meta_pretty = pformat(meta, indent=4, compact=True)
                    f.write(meta_pretty)
                    f.write("\n\n")
                f.write("\n\n")

    except:
        raise RuntimeError("Failed to export to summary!")


def export_bbox(dltile, outfile):
    """
    Export a DLTile to GeoJSON

    Parameters
    ----------
    dltile: dict
        DLTile specifying geocontext
    outfile: str
        Output GeoJSON file (.geojson)

    Raises
    ------
    RuntimeError
        If export to GeoJSON fails
    """

    try:
        features = [
            {"geometry": dltile["geometry"], "properties": None, "type": "Feature"}
        ]

        json_dict = {"type": "FeatureCollection", "features": features}

        with open(outfile, "w") as f:
            f.write(json.dumps(json_dict))

    except:
        raise RuntimeError("Bounding box export failed!")
