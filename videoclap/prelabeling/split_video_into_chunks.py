import os
import argparse
import random
import string

from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import VideoFileClip

parser = argparse.ArgumentParser(description='Automatic video labelling')

parser.add_argument('-f', '--video_dir', help='directory containing the video files to be pre-labelled')
parser.add_argument('-o', '--out_dir', help='directory to save the labels and images to')

args = parser.parse_args()

CHUNK_SIZE_SECONDS = 30

if __name__ == '__main__':

    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)

    video_file_names = os.listdir(args.video_dir)
    video_file_names = [f for f in video_file_names
                        if 'DS_Store' not in f
                        and not os.path.isdir(os.path.join(args.video_dir, f))]

    for video_file_name in video_file_names:
        print(video_file_name)

        video_path = os.path.join(args.video_dir, video_file_name)
        video = VideoFileClip(video_path)

        for i in range(int(video.duration // CHUNK_SIZE_SECONDS) + 1):
            letters = string.ascii_lowercase
            chunk_name = ''.join(random.choice(letters) for j in range(6)) + ".mp4"
            chunk_path = os.path.join(args.out_dir, chunk_name)

            ffmpeg_extract_subclip(video_path, i * CHUNK_SIZE_SECONDS, (i + 1) * CHUNK_SIZE_SECONDS, chunk_path)

            print("Saved {} - {} to {}".format(i * CHUNK_SIZE_SECONDS, (i + 1) * CHUNK_SIZE_SECONDS, chunk_path))



        print("-" * 100)
