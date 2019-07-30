import cv2
import numpy as np
import tensorflow as tf
import base64
import multiprocessing
from collections import namedtuple

from misc.utils import time_it

PredictionResult = namedtuple('PredictionResult', ['probabilities', 'saliency'])

class SavedModelClassifier:
    def __init__(self, saved_model_dir: str):
        self._session = tf.Session(config=tf.ConfigProto(
            device_count={'CPU': 1},
            inter_op_parallelism_threads=1, 
            allow_soft_placement=True,
            intra_op_parallelism_threads=multiprocessing.cpu_count())
        )

        tf.saved_model.load(self._session, [tf.saved_model.SERVING], saved_model_dir)

        self._image_bytes_placeholder = self._session.graph.get_tensor_by_name('image_bytes:0')
        self._saliency_tensor = self._session.graph.get_tensor_by_name('saliency:0')
        self._probabilities_tensor = self._session.graph.get_tensor_by_name('probabilities:0')

    def predict_jpeg(self, jpg_image_bytes: bytes) -> PredictionResult:
        with time_it('tf_predict'):
            probabilities, saliency = self._session.run([tf.squeeze(self._probabilities_tensor), tf.squeeze(self._saliency_tensor)], feed_dict={
                self._image_bytes_placeholder: jpg_image_bytes
            })

        return PredictionResult(probabilities, str(base64.b64encode(cv2.imencode('.jpeg', saliency)[1]), 'utf8'))
    
    def predict(self, image_bytes: bytes) -> PredictionResult:
        with time_it('decode_jpeg'):
            image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), 1)
            _, jpeg_bytes = cv2.imencode('.jpeg', image)

        return self.predict_jpeg(bytes(jpeg_bytes))
