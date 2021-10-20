import numpy as np


def convert_rectangle_to_polygon(rectangle_coordinates):
    a = np.array([rectangle_coordinates[0:2]])
    b = np.array([rectangle_coordinates[2:4]])
    c = np.array([[b[0][0], a[0][1]]])
    d = np.array([[a[0][0], b[0][1]]])

    return np.concatenate((a, c, b, d), axis=0).tolist()


def get_bbox(rectangle_coordinates):
    a = np.array([rectangle_coordinates[0:2]])
    b = np.array([rectangle_coordinates[2:4]])

    return np.concatenate((a, b), axis=0).tolist()

