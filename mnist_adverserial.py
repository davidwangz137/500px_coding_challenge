# Copyright 2015 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""A deep MNIST classifier using convolutional layers.

See extensive documentation at
https://www.tensorflow.org/get_started/mnist/pros
"""
# Disable linter warnings to maintain consistency with tutorial.
# pylint: disable=invalid-name
# pylint: disable=g-bad-import-order

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import sys

import logging
logging.getLogger("tensorflow").setLevel(logging.WARNING)

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data

class CNNMNIST():
    """CNNMNIST is a class that builds the graph for a deep net for classifying digits.

    Args:
      x: an input tensor with the dimensions (N_examples, 784), where 784 is the
      number of pixels in a standard MNIST image.

    Params:
      A tuple (y, keep_prob). y is a tensor of shape (N_examples, 10), with values
      equal to the logits of classifying the digit into one of 10 classes (the
      digits 0-9). keep_prob is a scalar placeholder for the probability of
      dropout.
    """
    def __init__(self, FLAGS):
        # Input placeholders
        if FLAGS.create_adv:
            x = tf.Variable(tf.zeros([FLAGS.batch_size, 784], dtype=tf.float32), trainable=False, name="x")
            x_input = tf.placeholder(tf.float32, [FLAGS.batch_size, 784], name="x_input")
            assign_x = x.assign(x_input)
        else:
            x = tf.placeholder(tf.float32, [FLAGS.batch_size, 784])
        y_ = tf.placeholder(tf.float32, [FLAGS.batch_size, 10], name="y_")
        keep_prob = tf.placeholder(tf.float32, name="keep_prob")
        self.placeholders = {'x':x, 'x_input':x_input, 'y_':y_, 'keep_prob':keep_prob}

        # Reshape to use within a convolutional neural net.
        # Last dimension is for "features" - there is only one here, since images are
        # grayscale -- it would be 3 for an RGB image, 4 for RGBA, etc.
        x_image = tf.reshape(x, [-1, 28, 28, 1])

        # First convolutional layer - maps one grayscale image to 32 feature maps.
        W_conv1 = weight_variable([5, 5, 1, 32])
        b_conv1 = bias_variable([32])
        h_conv1 = tf.nn.relu(conv2d(x_image, W_conv1) + b_conv1)

        # Pooling layer - downsamples by 2X.
        h_pool1 = max_pool_2x2(h_conv1)

        # Second convolutional layer -- maps 32 feature maps to 64.
        W_conv2 = weight_variable([5, 5, 32, 64])
        b_conv2 = bias_variable([64])
        h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)

        # Second pooling layer.
        h_pool2 = max_pool_2x2(h_conv2)

        # Fully connected layer 1 -- after 2 round of downsampling, our 28x28 image
        # is down to 7x7x64 feature maps -- maps this to 1024 features.
        W_fc1 = weight_variable([7 * 7 * 64, 1024])
        b_fc1 = bias_variable([1024])

        h_pool2_flat = tf.reshape(h_pool2, [-1, 7*7*64])
        h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)

        # Dropout - controls the complexity of the model, prevents co-adaptation of
        # features.
        h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

        # Map the 1024 features to 10 classes, one for each digit
        W_fc2 = weight_variable([1024, 10])
        b_fc2 = bias_variable([10])

        y_conv = tf.matmul(h_fc1_drop, W_fc2) + b_fc2

        # Loss function of model
        cross_entropy = tf.reduce_mean(
          tf.nn.softmax_cross_entropy_with_logits(labels=y_, logits=y_conv))
        optimizer = tf.train.AdamOptimizer(1e-4)
        train_op = optimizer.minimize(cross_entropy)
        self.optimizer = {'optimizer': optimizer, 'train_op': train_op}

        correct_prediction = tf.equal(tf.argmax(y_conv, 1), tf.argmax(y_, 1))
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
        self.output = {'logits_last':y_conv, 'cross_entropy':cross_entropy, 'accuracy': accuracy}

        # Additional ops of interest for debugging or experimentation
        self.ops = {'assign_x':assign_x}

    def prepare_feed_dict(self, x, y_, dropout_prob):
        return {model.placeholders['x']: x, model.placeholders['y_']: y_, model.placeholders['keep_prob']: dropout_prob}

'''
Convenience variable declaration, convolution and max_pooling functions so the code doesn't get ugly with the specifics
'''
def conv2d(x, W):
    """conv2d returns a 2d convolution layer with full stride."""
    return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')

def max_pool_2x2(x):
    """max_pool_2x2 downsamples a feature map by 2X."""
    return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],
                          strides=[1, 2, 2, 1], padding='SAME')

def weight_variable(shape):
    """weight_variable generates a weight variable of a given shape."""
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial, name='weight')

def bias_variable(shape):
    """bias_variable generates a bias variable of a given shape."""
    initial = tf.constant(0.1, shape=shape)
    return tf.Variable(initial, name='bias')

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('--data_dir', type=str,
                  default='/tmp/tensorflow/mnist/input_data',
                  help='Directory for storing input data')
parser.add_argument('--create_adv', action="store_true", default=False)
parser.add_argument('-batch_size', action="store", default=50, type=int)
FLAGS = parser.parse_args()

# Import data
mnist = input_data.read_data_sets(FLAGS.data_dir, one_hot=True)

# Create the model
tf.reset_default_graph()  # In case we are running this multiple times in a IPython session
model = CNNMNIST(FLAGS=FLAGS)

# Build the graph for the deep net

# Create the session and saver
sess = tf.Session()
trainable_vars = tf.trainable_variables()  # We can modify this to load only some of the variables using the Saver. I don't like this design but its not that bad... yet
saver = tf.train.Saver(var_list=trainable_vars, max_to_keep=0)  # Keep all checkpoints
sess.run(tf.global_variables_initializer())

if FLAGS.create_adv:
    logging.info("Creating adverserial examples!")

    # We load the model from before
    saver.restore(sess, 'model_checkpoints/mnist_deep.ckpt-200')
    batch = mnist.train.next_batch(FLAGS.batch_size)  # Sanity check
    train_accuracy = sess.run(model.output['accuracy'], feed_dict=model.prepare_feed_dict(x=batch[0], y_=batch[1], dropout_prob=1.0))
    print('training accuracy %g' % train_accuracy)  # Sanity check accuracy

    # Create adverserial images. Since we are trying to fool 2's specifically we minimize the softmax probability of it being a two. Or equivalently take the negative of the cross_entropy
    grad_tuple_list = model.optimizer['optimizer'].compute_gradients(-model.output['cross_entropy'], [model.placeholders['x']])
    grad_probs = grad_tuple_list[0][0]
    softmax_probs = tf.nn.softmax(model.output['logits_last'])

    twos = mnist.train.images[mnist.train.labels[:,2] == 1,:]  # NOTE: This looks like zeros unless you print the entire thing
    twos_adv = twos[:FLAGS.batch_size].copy()  # The images we are going to optimize in value
    twos_adv_start = twos[:FLAGS.batch_size].copy()  # The starting images for comparison
    labels_two = np.zeros((FLAGS.batch_size, 10))  # For computing the loss
    labels_two[:,2] = 1
    sess.run(model.ops['assign_x'], feed_dict={model.placeholders['x_input']: twos_adv})

    # Get and apply the gradients using numpy in a loop since the optimizer has momentum
    # NOTE: Different images have different twoness. Some require larger pushes and larger learning rates. So we might need to manually set learning rate for each image...
    # TODO: Set colorbar of plot by max and min range of images: [0,1]
    # TODO: Try directly optimizing the class probability of another label, whichever is the greatest already for the image.

    grad = sess.run(grad_probs, feed_dict={model.placeholders['y_']:labels_two, model.placeholders['keep_prob']:1.0})
    grad_norm = np.sqrt(np.sum(grad*grad, axis=1))

    learning_rate = 0.1
    log_ind = 2  # The index which to check the probability for
    print("Optimizing adverserial images!")
    for i in range(50):
        grad = sess.run(grad_probs, feed_dict={model.placeholders['y_']:labels_two, model.placeholders['keep_prob']:1.0})
        twos_adv -= learning_rate*grad
        sess.run(model.ops['assign_x'], feed_dict={model.placeholders['x_input']: twos_adv})
        probs = sess.run(softmax_probs, feed_dict={model.placeholders['keep_prob']:1.0})
        print(probs[log_ind])
        plt.imshow(twos_adv[log_ind].reshape((28, 28)), cmap='Greys')
        plt.savefig('plots/two_adv%d.png' % i)
    
    # Plot the images

    # Sanity check
    #x1 = sess.run(model.placeholders['x'])
    #sess.run(model.ops['assign_x'], feed_dict={model.placeholders['x_input']: np.ones((FLAGS.batch_size, 784))})
    #x2 = sess.run(model.placeholders['x'])
    # Sanity check 2
    #plt.imshow(twos[0].reshape((28,28)), cmap='Greys')
    #plt.show()

else:
    for i in range(20000):
        batch = mnist.train.next_batch(FLAGS.batch_size)
        if i % 100 == 0:
            train_accuracy = sess.run(model.output['accuracy'], feed_dict=model.prepare_feed_dict(x=batch[0], y_=batch[1], dropout_prob=1.0))
            print('step %d, training accuracy %g' % (i, train_accuracy))
            saver.save(sess, 'model_checkpoints/mnist_deep.ckpt', global_step=i)
        sess.run(model.optimizer['train_op'], feed_dict=model.prepare_feed_dict(x=batch[0], y_=batch[1], dropout_prob=0.5))

    # Get the test accuracy by looping over the test data in batches
    # NOTE: We need to convert the accuracy to a masked count of how many are correct. The masking deals with the fact that we might need to pad and ignore the label for the padding
    raise NotImplementedError
    print('test accuracy %g' % sess.run(model.output['accuracy'], feed_dict=model.prepare_feed_dict(x=mnist.test.images, y_=mnist.test.labels, dropout_prob=1.0)))

# Close the session so we don't pollute the IPython session on multiple runs
# TODO: If we have a GPU already allocated, then might be faster to not close and keep the old session around. Test this
sess.close()
