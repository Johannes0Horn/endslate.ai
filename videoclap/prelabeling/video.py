import cv2
from secrets import token_hex

from prelabeling.annotation_object import AnnotationObject


class Video:

    def __init__(self, video_path):
        self.cap = cv2.VideoCapture(video_path)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.key = token_hex(16)

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        _, image = self.cap.read()

        if image is None:
            print("None in image")
            return

        self.width = image.shape[1]
        self.height = image.shape[0]

        self.annotations = list()

    def add_annotation(self, annotation_object):
        self.annotations.append(annotation_object)

    def get_latest_annotation(self):
        return self.annotations[-1]

    def add_frame(self, class_name, frame_number, coordinates, geometry_type):
        for annotation in self.annotations:
            annotation_class_name = annotation.class_title

            if annotation_class_name == class_name:
                annotation.add_frame(frame_number, coordinates, geometry_type)
                return

        annotation = AnnotationObject(class_title=class_name, tags=[])
        annotation.add_frame(frame_number, coordinates, geometry_type)
        self.annotations.append(annotation)

    def get_frame(self, frame_number):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        _, image = self.cap.read()
        return image

    def get_total_frames(self):
        return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def create_json_string(self):
        objects = self.create_annotation_entries()
        frames = self.create_frame_entries()

        json_string = {
            "size": {
                "width": self.width,
                "height": self.height
            },
            "description": "",
            "key": self.key,
            "tags": [],
            "objects": objects,
            "frames": frames,
            "framesCount": self.frame_count
        }

        return json_string

    def create_annotation_entries(self):
        objects = list()

        for annotation in self.annotations:
            entry = annotation.get_json_representation()
            objects.append(entry)

        return objects

    def create_frame_entries(self):
        entries = list()

        for annotation in self.annotations:
            for frame in annotation.frames:
                entries.append(frame.get_json_representation())

        return entries

    def create_key_id_map(self):
        key_id_map = {
            "tags": {},
            "objects": {},
            "figures": {},
            "videos": {
                str(self.key): 157230088
            }
        }

        for i, annotation in enumerate(self.annotations):
            key_id_map["objects"][annotation.key] = 3000 + i

        frame_counter = 449627028
        for annotation in self.annotations:
            for frame in annotation.frames:
                key_id_map["figures"][frame.key] = frame_counter
                frame_counter += 1

        return key_id_map
