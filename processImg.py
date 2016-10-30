
# get original number of pixels

# if width > height, crop width = height / width, if height > width, crop height = width / height

# get number of current pixels

# if square crop < k% of original pixels then we dont do anything

# otherwise we crop image where fx = fy = sqrt(currSize / k%origsize)

# now we rescale the image to preset size, e.g. 64 * 64, or maybe we store multiple sizes????

import math
import cv2
import numpy as np
import sys

def get_factors(width, height):

    if width > height:
        return height / width, 1

    return 1, width / height


def crop_square(img):
    height, width, _ = img.shape
    if width > height:
        start = int((width - height) / 2)
        return img[:height, start:start+height]

    start = int((height - width) / 2)
    return img[start:start+width, :width]


def crop(orig_width, orig_height, factor, img):
    new_height, new_width, _ = img.shape

    new_pix = new_width * new_height
    orig_pix = orig_width * orig_height

    if new_pix > orig_pix * factor:
        scale = math.sqrt((orig_pix * factor) / new_pix)

        scaled_width = scale * new_width
        scaled_height = scale * new_height

        startx = (new_width - scaled_width) / 2
        starty = (new_height - scaled_height) / 2

        return img[starty:scaled_height, startx:scaled_width]



targetx = 108
targety = 108

content = np.fromstring(open(sys.argv[1], 'rb').read(), np.uint8)
testimg = cv2.imdecode(content, 1)

testimg = crop_square(testimg)
height, width, _ = testimg.shape

scaled = cv2.resize(testimg, None, fx=targetx/width, fy=targety/height, interpolation=cv2.INTER_CUBIC)

cv2.imwrite('.'.join(['mod'] + sys.argv[1].split('.')), scaled)
