"""
tensorflow backend (https://github.com/tensorflow/tensorflow)
"""

# pylint: disable=unused-argument,missing-docstring

import tensorflow as tf
from tensorflow.core.framework import graph_pb2

import backend


class BackendTensorflow(backend.Backend):
    def __init__(self):
        super(BackendTensorflow, self).__init__()

    def version(self):
        return tf.__version__ + "/" + tf.__git_version__

    def name(self):
        return "tensorflow"

    def image_format(self):
        return "NHWC"

    def load(self, model_path, inputs=None, outputs=None):
        if not inputs:
            raise ValueError("BackendTensorflow needs inputs")
        if not outputs:
            raise ValueError("BackendTensorflow needs outputs")
        # TODO: support checkpoint and saved_model formats?
        graph_def = graph_pb2.GraphDef()
        with open(model_path, "rb") as f:
            graph_def.ParseFromString(f.read())

        g = tf.import_graph_def(graph_def, name='')
        self.sess = tf.Session(graph=g)
        self.outputs = outputs
        self.inputs = inputs
        return self

    def predict(self, feed):
        return self.sess.run(self.outputs, feed_dict=feed)
