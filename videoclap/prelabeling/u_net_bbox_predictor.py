import os

import cv2
import numpy as np

from skimage.color import rgb2gray
from skimage.transform import resize

os.environ["KERAS_BACKEND"] = "plaidml.keras.backend"

from keras.models import load_model


class UNetBBoxPredictor:

    def __init__(self, segmentation_model_path, classifier_path):
        self.segmentation_model = load_model(segmentation_model_path, compile=False)
        print("Loaded {}".format(segmentation_model_path))

        self.classification_model = load_model(classifier_path, compile=False)
        print("Loaded ", classifier_path)

    def predict(self, image):
        img_edited = resize(image, (224, 224))
        img_edited = np.expand_dims(img_edited, axis=0)

        mask = self.segmentation_model.predict(img_edited)
        mask = np.around(mask)
        mask = resize(mask[0, :, :, 0], (image.shape[0], image.shape[1]))

        contours, hierarchy = cv2.findContours(mask.astype(np.uint8), 1, 2)

        if len(contours) > 0:
            cnt = contours[0]
            bbox = cv2.boundingRect(cnt)

            x_min = bbox[0]
            x_max = bbox[0] + bbox[2]
            y_min = bbox[1]
            y_max = bbox[1] + bbox[3]

            # Classify the cropped image
            img_cropped = image[y_min:y_max, x_min:x_max]
            img_cropped = resize(img_cropped, (224, 224))
            img_cropped = rgb2gray(img_cropped)

            img_cropped = np.expand_dims(img_cropped, axis=0)
            img_cropped = np.expand_dims(img_cropped, axis=3)

            confidence = self.classification_model.predict(img_cropped)[0][0]
            y_hat = int(np.around(confidence))
            posterior = self.get_posterior_probability(confidence)

            return np.array([x_min, y_min, x_max, y_max, y_hat, posterior])
        else:
            return []

    def get_posterior_probability(self, confidence):
        """
        Posterior probability for a two class classification problem from 0 to 1 for each class
        :param confidence: confidence value from the sigmoid function
        :return: posterior probability between 0 and 1
        """

        class_index = np.around(confidence)

        if class_index == 1:
            return confidence
        else:
            return 1 - confidence

