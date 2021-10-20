from secrets import token_hex
from prelabeling.frame import Frame


class AnnotationObject:

    def __init__(self, class_title, tags):
        self.class_title = class_title
        self.tags = tags
        self.frames = list()

        self.key = token_hex(16)

    def add_frame(self, frame_number, points, geometry_type='polygon'):
        frame = Frame(frame_number, geometry_type, points, self.key)
        self.frames.append(frame)

    def get_json_representation(self):
        rep = {
            "key": self.key,
            "classTitle": self.class_title,
            "tags": self.tags
        }

        return rep
