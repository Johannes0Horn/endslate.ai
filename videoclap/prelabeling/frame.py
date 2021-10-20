from secrets import token_hex


class Frame:

    def __init__(self, frame_number, geometry_type, points, annotation_object_key):
        self.frame_number = frame_number
        self.geometry_type = geometry_type
        self.points = points
        self.object_key = annotation_object_key
        self.key = token_hex(16)

    def get_json_representation(self):
        rep = {
            "index": self.frame_number,
            "figures": [
                {
                    "key": self.key,
                    "objectKey": self.object_key,
                    "geometryType": self.geometry_type,
                    "geometry": {
                        "points": {
                            "exterior": self.points,
                            "interior": []
                        }
                    }
                }
            ]
        }

        return rep
