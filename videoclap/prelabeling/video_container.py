import json
import os
from secrets import token_hex
from shutil import copyfile

from prelabeling.file_handling import create_directory_structure_video
from prelabeling.json_creation import create_meta_json
from prelabeling.video_annotator import VideoAnnotator


class VideoContainer:

    def __init__(self, video_dir, out_dir, yolo):
        self.yolo = yolo
        self.out_dir = out_dir
        self.video_dir = video_dir
        self.videos = list()
        self.key = token_hex(16)

        # create directory structure
        self.create_directories()
        self.create_meta_json()

    def get_already_processed_files(self):
        out_video_path = os.path.join(self.out_dir, 'dataset', 'video')
        return os.listdir(out_video_path)

    def create_meta_json(self):
        meta_json_content = create_meta_json(geometry_type='rectangle')

        with open(os.path.join(self.out_dir, 'meta.json'), "w") as meta:
            json.dump(meta_json_content, meta)

    def create_dirs_if_not_exists(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def create_directories(self):
        self.create_dirs_if_not_exists(os.path.join(self.out_dir, 'dataset', 'video'))
        self.create_dirs_if_not_exists(os.path.join(self.out_dir, 'dataset', 'ann'))

    def annotate_videos(self):

        # Remove DS_Store, directories
        files = [f for f in os.listdir(self.video_dir)
                 if 'DS_Store' not in f
                 and not os.path.isdir(os.path.join(self.video_dir, f))]

        for i, video_file_name in enumerate(files):
            print("{} - {}/{}".format(video_file_name, i + 1, len(files)))

            video_file_path = os.path.join(self.out_dir, 'dataset', 'video', video_file_name)
            video_ann_path = os.path.join(self.out_dir, 'dataset', 'ann', video_file_name.split('.')[0] + '.json')
            video_source = os.path.join(self.video_dir, video_file_name)

            video_ann = VideoAnnotator(video_source, self.yolo)
            video_ann.annotate_frames()

            try:
                # Save JSON annotation containing the video file
                json_annotation = video_ann.video.create_json_string()

                with open(video_ann_path, 'w') as json_file:
                    json.dump(json_annotation, json_file)
                    json_file.close()

                print("Saved {}".format(video_ann_path))

                # Copy the original video file to the annotations folder
                copyfile(video_source, video_file_path)

                print("Copied {} to {}".format(video_source, video_file_path))

                # Append the video along with the annotations to the video list
                self.videos.append(video_ann.video)

                print("-" * 100)
            except:
                print("Error processing file ", video_file_name)

        key_id_map = self.create_key_id_map()
        key_id_map_path = os.path.join(self.out_dir, 'key_id_map.json')

        with open(key_id_map_path, 'w') as json_file:
            json.dump(key_id_map, json_file)
            json_file.close()

        print("Saved key_id_map to {}".format(key_id_map_path))

    def add_video(self, video):
        self.videos.append(video)

    def get_annotations(self):
        all_annototation_objects = list()

        for video in self.videos:
            for annotation in video.annotations:
                all_annototation_objects.append(annotation)

        return all_annototation_objects

    def get_frames(self):
        all_figures = list()

        for video in self.videos:
            for annotation in video.annotations:
                for frame in annotation.frames:
                    all_figures.append(frame)

        return all_figures

    def create_key_id_map(self):
        key_id_map = {
            "tags": {},
            "objects": {},
            "figures": {},
            "videos": {}
        }

        for i, annotation in enumerate(self.get_annotations()):
            key_id_map["objects"][annotation.key] = 3000 + i

        for i, frame in enumerate(self.get_frames()):
            key_id_map["figures"][frame.key] = 449627028 + i

        for i, video in enumerate(self.videos):
            key_id_map["videos"][video.key] = 157230088 + i

        return key_id_map
