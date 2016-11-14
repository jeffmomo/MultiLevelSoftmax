import tensorflow as tf
import numpy as np
import threading
import time


queue = tf.FIFOQueue(capacity=100, dtypes=tf.int32)

queue_list = []


testerino = queue.dequeue() + 1

init = tf.initialize_all_variables()

# Launch the graph.
sess = tf.Session()
sess.run(init)

main_thread_graph = tf.get_default_graph()

def runFeeder():
    with main_thread_graph.as_default():
        while True:
            f = open('./pipe', 'r')
            lines = f.readlines()
            ls = []
            for line in lines:
                ls.extend([int(x) for x in line.split(">>>EOF<<<")[:-1]])

            conv = tf.convert_to_tensor(ls, tf.int32)
            # print(conv)
            enqueue_op = queue.enqueue_many(vals=conv)
            sess.run(enqueue_op)

feedThread = threading.Thread(target=runFeeder)
feedThread.start()



for step in range(201):
    print(sess.run(testerino))


