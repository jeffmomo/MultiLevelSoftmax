import threading
import time
import cv2
import base64
import numpy as np

def runFeeder():
    while True:
        f = open('./pipe', 'r')
        lines = f.readlines()
        ls = []
        for line in lines:
            ls.extend([ (np.frombuffer(base64.standard_b64decode(x[0]), np.uint8), int(x[1])) for x in [x.split('>>>INDEX<<<') for x in line.split(">>>EOF<<<")[:-1]]])

        for img, idx in ls:
            img_np = cv2.imdecode(img, 1)
            print('img recvd: ' + str(idx))
            cv2.startWindowThread()
            cv2.namedWindow("preview")
            cv2.imshow("preview", img_np)


feedThread = threading.Thread(target=runFeeder)
feedThread.start()




