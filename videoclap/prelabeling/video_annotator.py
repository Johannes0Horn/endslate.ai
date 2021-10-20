import numpy as np
from tqdm import tqdm

from prelabeling import utils
from prelabeling.video import Video
from config import CLASS_NAMES


def correct_out_of_bounds(image_shape, bbox_coordinates):
    bbox_coordinates = correct_positive_out_of_bounds(bbox_coordinates, image_shape)
    bbox_coordinates = correct_negative_out_of_bounds(bbox_coordinates)

    return bbox_coordinates


def correct_negative_out_of_bounds(bbox_coordinates):
    # x_min
    if bbox_coordinates[0] < 0:
        bbox_coordinates[0] = 0

    # y_min
    if bbox_coordinates[1] < 0:
        bbox_coordinates[1] = 0

    # x_max
    if bbox_coordinates[2] < 0:
        bbox_coordinates[2] = 0

    # y_max
    if bbox_coordinates[3] < 0:
        bbox_coordinates[3] = 0

    return bbox_coordinates


def correct_positive_out_of_bounds(bbox_coordinates, image_shape):
    # x_min
    if bbox_coordinates[0] >= image_shape[1]:
        bbox_coordinates[0] = image_shape[1] - 1

    # y_min
    if bbox_coordinates[1] >= image_shape[0]:
        bbox_coordinates[1] = image_shape[0] - 1

    # x_max
    if bbox_coordinates[2] >= image_shape[1]:
        bbox_coordinates[2] = image_shape[1] - 1

    # y_max
    if bbox_coordinates[3] >= image_shape[0]:
        bbox_coordinates[3] = image_shape[0] - 1

    return bbox_coordinates


class VideoAnnotator():

    def __init__(self, video_path: object, yolo: object) -> object:
        self.video = Video(video_path)
        self.yolo = yolo

    def annotate_frames(self):

        for frame_number in tqdm(range(self.video.get_total_frames())):

            image = self.video.get_frame(frame_number)

            if image is not None:

                prediction = self.yolo.predict(image)
                if len(prediction) > 0:
                    self.add_annotation(prediction, frame_number, image.shape)

    def add_annotation(self, prediction, frame_number, image_shape):

        bbox_coordinates = prediction[:4].astype(np.int32)
        bbox_coordinates = correct_out_of_bounds(image_shape, bbox_coordinates)

        current_class_index = int(prediction[4])

        self.video.add_frame(class_name=CLASS_NAMES[current_class_index],
                             frame_number=frame_number,
                             coordinates=utils.get_bbox(bbox_coordinates),
                             geometry_type='rectangle')

        return current_class_index

    @staticmethod
    def get_best_prediction(predictions):
        highest_confidence = 0.
        best_prediction = None

        for prediction in predictions:
            confidence = prediction[4]

            if confidence > highest_confidence:
                best_prediction = prediction

        return best_prediction
