#!/bin/sh


python prelabel_video_to_video.py -f ../data/obj_det_data/train_videos/slate_fairy_kook.mp4 -o ../data/obj_det_data/train_videos/supervisely -p slate_fairy_kook
python prelabel_video_to_video.py -f ../data/obj_det_data/train_videos/video.mp4 -o ../data/obj_det_data/train_videos/supervisely -p inglorious_basterds
python prelabel_video_to_video.py -f ../data/obj_det_data/train_videos/what_clapperboard.mp4 -o ../data/obj_det_data/train_videos/supervisely -p what_clapperboard
python prelabel_video_to_video.py -f ../data/obj_det_data/train_videos/why_clapperboard.mp4 -o ../data/obj_det_data/train_videos/supervisely -p why_clapperboard
python prelabel_video_to_video.py -f ../data/obj_det_data/train_videos/how_to_slate.mp4 -o ../data/obj_det_data/train_videos/supervisely -p how_to_slate

