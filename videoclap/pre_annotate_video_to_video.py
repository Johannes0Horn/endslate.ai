import argparse

#from evaluate import YoloTest

from prelabeling.u_net_bbox_predictor import UNetBBoxPredictor
from prelabeling.video_container import VideoContainer

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Automatic video labelling')

    parser.add_argument('-f', '--video_dir', help='directory containing the video files to be pre-labelled')
    parser.add_argument('-o', '--out_dir', help='directory to save the labels and images to')

    args = parser.parse_args()

    #yolo = YoloTest()

    bbox_predictor = UNetBBoxPredictor('../video-analyzer/models/linknet_bbox_predictor.h5',
                                       '../video-analyzer/models/mobilenet_v5.h5')

    video_container = VideoContainer(args.video_dir, args.out_dir, bbox_predictor)
    video_container.annotate_videos()

