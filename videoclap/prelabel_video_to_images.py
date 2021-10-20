import cv2
import os
import json
import argparse

from evaluate import YoloTest
from prelabeling import utils
from prelabeling.json_creation import create_json_content, create_meta_json
from prelabeling.file_handling import create_directory_structure

from config import CLASS_NAMES

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Automatic video labelling')

    parser.add_argument('-f', '--file', help='video file')
    parser.add_argument('-o', '--out_dir', help='directory to save the labels and images to')
    parser.add_argument('-p', '--project_name', help='project name for supervisely')

    args = parser.parse_args()

    yolo = YoloTest()

    # create directory structure
    proj_dir, ann_dir, img_dir = create_directory_structure(args.out_dir, args.project_name)
    meta_json_content = create_meta_json()

    with open(os.path.join(args.out_dir, 'meta.json'), "w") as meta:
        json.dump(meta_json_content, meta)

    # iterate through the video
    cap = cv2.VideoCapture(args.file)
    success, img = cap.read()
    fno = 0

    while success:
        # read next frame
        success, img = cap.read()
        try:
            prediction = yolo.predict(img)

            json_content = create_json_content(prediction, img.shape[1], img.shape[0])

            ann_file_path = os.path.join(ann_dir, "{}.{}".format(str(fno), "json"))
            img_file_path = os.path.join(img_dir, "{}.{}".format(str(fno), "jpg"))

            fno += 1

            with open(ann_file_path, 'w') as json_file:
                json.dump(json_content, json_file)
                json_file.close()

            cv2.imwrite(img_file_path, img)

            print("Saved {} - {}".format(ann_file_path, img_file_path))
            print("-" * 100)
        except:
            print("End of file")
