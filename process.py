import uuid
import threading
import requests
import os.path
import math
import cv2
import numpy as np
import hashlib

f = open('observations.csv', 'r')
imgs = open('images.csv', 'r')
out = open('output.csv', 'w')

written = open('notwritten.txt', 'w+')
written_links = []
for line in written:
    written_links.append(line)


def get_factors(width, height):
    if width > height:
        return height / width, 1

    return 1, width / height


def crop_square(img):
    height, width, _ = img.shape
    if width > height:
        start = int((width - height) / 2)
        return img[:height, start:start + height]

    start = int((height - width) / 2)
    return img[start:start + width, :width]


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


def genId(link):
    return str(hashlib.sha224(link).hexdigest())


def writeFile(name, content_type, link):
    filetype, extension = content_type.split("/")

    if link in written_links:
        return False

    if filetype == "image":
        res = requests.get(link)
        if res.status_code == 200:
            path = os.path.join("./images", name + "." + extension)

            targetx = 256
            targety = 256

            img_bytes = np.fromstring(res.content, np.uint8)
            testimg = cv2.imdecode(img_bytes, 1)
            testimg = crop_square(testimg)
            height, width, _ = testimg.shape
            scaled = cv2.resize(testimg, None, fx=targetx / width, fy=targety / height, interpolation=cv2.INTER_LANCZOS4)

            cv2.imwrite(path, scaled)
            written.write(link + "\n")

            return True
        else:
            print("not written " + link + "\n")

    else:
        print(name + "|" + link + "\n")
        print("not image found")

    return False

hashmap = {}
links = []

for line in f:
    id, *rest = line.split(',')
    hashmap[id] = line[:-1]

for line in imgs:
    id, type, content_type, link, *rest = line.split(',')
    if id in hashmap:
        ident = genId(link)
        out.write(hashmap[id] + '|_|' + ','.join([type, content_type, ident]) + '\n')
        links.append((link, ident, content_type))

lock = threading.Lock()
plock = threading.Lock()


def downloadOne():
    while True:
        lock.acquire()
        if not len(links):
            break
        link, id, content_type = links.pop()
        lock.release()
        writeFile(id, content_type, link)
        plock.acquire()
        print(link, id)
        plock.release()

    lock.release()


for i in [threading.Thread(target=downloadOne) for t in range(0, 20)]:
    i.start()

out.close()
f.close()
imgs.close()
