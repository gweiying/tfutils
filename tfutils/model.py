from __future__ import absolute_import, division, print_function
from collections import OrderedDict

import numpy as np
import tensorflow as tf


class ConvNet(object):
    """Basic implementation of ConvNet class compatible with tfutils.
    """

    def __init__(self, seed=None, **kwargs):
        self.seed = seed
        self.output = None
        self._params = OrderedDict()

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, value):
        name = tf.get_variable_scope().name
        if name not in self._params:
            self._params[name] = OrderedDict()
        self._params[name][value['type']] = value

    @property
    def graph(self):
        return tf.get_default_graph().as_graph_def()

    def initializer(self, kind='xavier', stddev=.1):
        if kind == 'xavier':
            init = tf.contrib.layers.initializers.xavier_initializer(seed=self.seed)
        elif kind == 'trunc_norm':
            init = tf.truncated_normal_initializer(mean=0, stddev=stddev, seed=self.seed)
        else:
            raise ValueError('Please provide an appropriate initialization '
                             'method: xavier or trunc_norm')
        return init

    def conv(self,
             out_shape,
             ksize=3,
             stride=1,
             padding='SAME',
             init='xavier',
             stddev=.01,
             bias=1,
             activation='relu',
             weight_decay=None,
             in_layer=None):
        if in_layer is None: in_layer = self.output
        if weight_decay is None: weight_decay = 0.
        in_shape = in_layer.get_shape().as_list()[-1]

        if isinstance(ksize, int):
            ksize1 = ksize
            ksize2 = ksize
        else:
            ksize1, ksize2 = ksize

        kernel = tf.get_variable(initializer=self.initializer(init, stddev=stddev),
                                 shape=[ksize1, ksize2, in_shape, out_shape],
                                 dtype=tf.float32,
                                 regularizer=tf.contrib.layers.l2_regularizer(weight_decay),
                                 name='weights')
        conv = tf.nn.conv2d(in_layer, kernel,
                            strides=[1, stride, stride, 1],
                            padding=padding)
        biases = tf.get_variable(initializer=tf.constant_initializer(bias),
                                 shape=[out_shape],
                                 dtype=tf.float32,
                                 name='bias')
        out = tf.nn.bias_add(conv, biases, name='conv')
        if activation is not None:
            out = self.activation(out, kind=activation)
        self.params = {'input': in_layer.name,
                       'type': 'conv',
                       'num_filters': out_shape,
                       'stride': stride,
                       'kernel_size': (ksize1, ksize2),
                       'padding': padding,
                       'init': init,
                       'stddev': stddev,
                       'bias': bias,
                       'activation': activation,
                       'weight_decay': weight_decay,
                       'seed': self.seed}
        self.output = out
        return self.output

    def fc(self,
           out_shape,
           init='xavier',
           stddev=.01,
           bias=1,
           activation='relu',
           dropout=.5,
           in_layer=None):
        if in_layer is None: in_layer = self.output
        resh = tf.reshape(in_layer,
                          [in_layer.get_shape().as_list()[0], -1],
                          name='reshape')
        in_shape = resh.get_shape().as_list()[-1]

        kernel = tf.get_variable(initializer=self.initializer(init, stddev=stddev),
                                 shape=[in_shape, out_shape],
                                 dtype=tf.float32,
                                 name='weights')
        biases = tf.get_variable(initializer=tf.constant_initializer(bias),
                                 shape=[out_shape],
                                 dtype=tf.float32,
                                 name='bias')
        fcm = tf.matmul(resh, kernel)
        out = tf.nn.bias_add(fcm, biases, name='fc')
        if activation is not None:
            out = self.activation(out, kind=activation)
        if dropout is not None:
            out = self.dropout(out)

        self.params = {'input': in_layer.name,
                       'type': 'fc',
                       'num_filters': out_shape,
                       'init': init,
                       'bias': bias,
                       'stddev': stddev,
                       'activation': activation,
                       'dropout': dropout,
                       'seed': self.seed}
        self.output = out
        return self.output

    def norm(self,
             depth_radius=2,
             bias=1,
             alpha=2e-5,
             beta=.75,
             in_layer=None):
        if in_layer is None: in_layer = self.output
        self.output = tf.nn.lrn(in_layer,
                                depth_radius=np.float(depth_radius),
                                bias=np.float(bias),
                                alpha=alpha,
                                beta=beta,
                                name='norm')
        self.params = {'input': in_layer.name,
                       'type': 'lrnorm',
                       'depth_radius': depth_radius,
                       'bias': bias,
                       'alpha': alpha,
                       'beta': beta}
        return self.output

    def pool(self,
             ksize=3,
             stride=2,
             padding='SAME',
             in_layer=None):
        if in_layer is None: in_layer = self.output

        if isinstance(ksize, int):
            ksize1 = ksize
            ksize2 = ksize
        else:
            ksize1, ksize2 = ksize

        self.output = tf.nn.max_pool(in_layer,
                                     ksize=[1, ksize1, ksize2, 1],
                                     strides=[1, stride, stride, 1],
                                     padding=padding,
                                     name='pool')
        self.params = {'input': in_layer.name,
                       'type': 'maxpool',
                       'kernel_size': (ksize1, ksize2),
                       'stride': stride,
                       'padding': padding}
        return self.output

    def activation(self, in_layer, kind='relu'):
        if kind == 'relu':
            out = tf.nn.relu(in_layer, name='relu')
        else:
            raise ValueError("Activation '{}' not defined".format(kind))
        return out

    def dropout(self, in_layer, dropout=.5):
        drop = tf.nn.dropout(in_layer, dropout, seed=self.seed, name='dropout')
        return drop


def alexnet(inputs, **kwargs):
    m = ConvNet(**kwargs)

    with tf.variable_scope('conv1'):
        m.conv(64, 11, 4, stddev=.01, bias=0, activation='relu', in_layer=inputs)
        m.norm(depth_radius=4, bias=1, alpha=.001 / 9.0, beta=.75)
        m.pool(3, 2)

    with tf.variable_scope('conv2'):
        m.conv(192, 5, 1, stddev=.01, bias=1, activation='relu')
        m.norm(depth_radius=4, bias=1, alpha=.001 / 9.0, beta=.75)
        m.pool(3, 2)

    with tf.variable_scope('conv3'):
        m.conv(384, 3, 1, stddev=.01, bias=0, activation='relu')

    with tf.variable_scope('conv4'):
        m.conv(256, 3, 1, stddev=.01, bias=1, activation='relu')

    with tf.variable_scope('conv5'):
        m.conv(256, 3, 1, stddev=.01, bias=1, activation='relu')
        m.pool(3, 2)

    with tf.variable_scope('fc6'):
        m.fc(4096, stddev=.01, bias=1, activation='relu', dropout=.5)

    with tf.variable_scope('fc7'):
        m.fc(4096, stddev=.01, bias=1, activation='relu', dropout=.5)

    with tf.variable_scope('fc8'):
        m.fc(1000, stddev=.01, bias=0, activation=None, dropout=None)

    return m


def alexnet_tfutils(inputs, **kwargs):
    m = alexnet(inputs['data'], **kwargs)
    return m.output, m.params