import random

import numpy as np

from prelabeling import utils
from config import CLASS_NAMES


def create_meta_json(geometry_type='polygon'):
    meta = {"classes": list()}

    for cls in CLASS_NAMES.values():
        r = lambda: random.randint(0, 255)
        color = '#%02X%02X%02X' % (r(), r(), r())

        cls_json = {
            "title": cls,
            "shape": geometry_type,
            "color": color
        }

        meta['classes'].append(cls_json)

    return meta


def create_entry(class_name, coordinates):

    return {
        "description": "",
        "tags": [],
        "bitmap": None,
        "classTitle": class_name,
        "geometryType": "polygon",
        "points": {
            "exterior": coordinates,
            "interior": []
        }
    }


def create_json_content(predictions, width, height):
    if len(predictions) > 0:
        entries = create_entries(predictions)
    else:
        entries = []

    return {
        "description": "",
        "tags": [],
        "size": {
            "width": width,
            "height": height
        },
        "objects": entries
    }


def create_entries(predictions):
    entries = list()

    for prediction in predictions:
        bbox_coordinates = prediction[:4].astype(np.int32)
        polygon_coordinates = utils.convert_rectangle_to_polygon(bbox_coordinates)

        class_index = int(prediction[5])
        class_name = CLASS_NAMES[class_index]

        json_entry = create_entry(class_name, polygon_coordinates)
        entries.append(json_entry)

    return entries


