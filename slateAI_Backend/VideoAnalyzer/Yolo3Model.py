import tensorflow as tf
import VideoAnalyzer.core.utils as utils
import numpy as np

class Yolo3Model:
    def __init__(self, modelpath):
        self.input_size = 544
        self.num_classes = 2
        self.graph = tf.Graph()
        self.return_elements = ["input/input_data:0", "pred_sbbox/concat_2:0", "pred_mbbox/concat_2:0", "pred_lbbox/concat_2:0"]
        print(modelpath)
        self.return_tensors = utils.read_pb_return_tensors(self.graph, modelpath, self.return_elements)
        self.sess  = tf.Session(graph=self.graph)
        self.confidence_threshold = 0.85
        


    def predict(self, image):
        # image preprocessing
        org_image = np.copy(image)
        org_h, org_w, _ = org_image.shape
        image_data = utils.image_preporcess(np.copy(image), [self.input_size, self.input_size])
        image_data = image_data[np.newaxis, ...]
        # run NN
        pred_sbbox, pred_mbbox, pred_lbbox = self.sess.run(
            [self.return_tensors[1], self.return_tensors[2], self.return_tensors[3]],
                    feed_dict={ self.return_tensors[0]: image_data})
        # postprocessing
        pred_bbox = np.concatenate([np.reshape(pred_sbbox, (-1, 5 + self.num_classes)),
                                    np.reshape(pred_mbbox, (-1, 5 + self.num_classes)),
                                    np.reshape(pred_lbbox, (-1, 5 + self.num_classes))], axis=0)
        bboxes = utils.postprocess_boxes(pred_bbox, (org_h, org_w), self.input_size, self.confidence_threshold)
        #filter bboxes
        bboxes = utils.nms(bboxes, 0.45, method='nms')

        return  bboxes

        # use this to return a class only
        """
         #make to numpy array
        bboxes = np.array(bboxes)
        #keep indexes 4 und 5 of all rows (=prop & class)
        bboxes = bboxes[:,4:6]
        if more than 1 bbox, keep the one with highest prob
        if len(bboxes) > 1:
            # select rows where prob equals max of probs
            bboxes = bboxes[bboxes[:,0] == np.amax(bboxes, axis=0)]
            
        if bboxes[0][1]==1.0:
            return "open"
        else:
            return "closed"   
        """


        pred_bbox = np.concatenate([np.reshape(pred_sbbox, (-1, 5 + self.num_classes)),
                                    np.reshape(pred_mbbox, (-1, 5 + self.num_classes)),
                                    np.reshape(pred_lbbox, (-1, 5 + self.num_classes))], axis=0)
        bboxes = utils.postprocess_boxes(pred_bbox, (org_h, org_w), self.input_size, self.score_threshold)
        bboxes = utils.nms(bboxes, self.iou_threshold)

        return bboxes