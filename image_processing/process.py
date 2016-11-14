import csv
import threading
import requests
import os.path
import math
import cv2
import numpy as np
import base64

f = open('observations.csv', 'r')
imgs = open('images.csv', 'r')
out = open('output.csv', 'w')

written = open('notwritten.txt', 'a+')
written.seek(0)

written_links = set()
for line in written:
    # gets rid of \n
    written_links.add(line[:-1])


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


def gen_id(link):
    return base64.urlsafe_b64encode(link.encode('utf-8')).decode('utf-8')


def write_file(name, content_type, link):
    
    ctype = content_type.split("/")
    if len(ctype) < 2:
        print('strange content type ' + content_type)
        return False

    filetype, extension = ctype

    if link in written_links:
        return True

    if filetype == "image":
        res = requests.get(link)

        if res.status_code == 200:
            path = os.path.join("./images", name + "." + extension)

            targetx = 256
            targety = 256

            img_bytes = np.fromstring(res.content, np.uint8)

            testimg = None
            try:
                testimg = cv2.imdecode(img_bytes, 1)
            except Exception:
                pass

            if testimg is None:
                print("image not decodable")
                return False

            testimg = crop_square(testimg)

            height, width, _ = testimg.shape
            scaled = cv2.resize(testimg, None, fx=targetx / width, fy=targety / height, interpolation=cv2.INTER_LANCZOS4)

            cv2.imwrite(path, scaled)
            written.write(link + "\n")

            return True
        else:
            print(" request unsuccessful " + link + "\n")

    else:
        print(filetype + " " + link + "\n")
        print("type is not image")

    return False

hashmap = {}
links = []

csv_obs = csv.reader(f, delimiter=',', quotechar='"')
csv_imgs = csv.reader(imgs, delimiter=',', quotechar='"')

for line in csv_obs:
    id, *rest = line
    hashmap[id] = line

for line in csv_imgs:
    id, type, content_type, link, *rest = line
    if id in hashmap:
        ident = gen_id(link)
        out.write('_._'.join(hashmap[id]) + '|_|' + '_._'.join([type, content_type, ident]) + '\n')
        links.append((link, ident, content_type))


MAX_THREADS = 50
lock = threading.Lock()
plock = threading.Lock()
semaphore = threading.BoundedSemaphore(MAX_THREADS)


def downloadOne():
    semaphore.acquire()
    while True:
        lock.acquire()
        if not len(links):
            break
        link, id, content_type = links.pop()
        lock.release()

        success = False
        try:
            success = write_file(id, content_type, link)
        except Exception as ex:
            semaphore.release()
            return

        if not success:
            plock.acquire()
            print(link, id)
            plock.release()

    lock.release()
    semaphore.release()


def monitor_threads():
    while True:
        lock.acquire()
        if not len(links):
            plock.acquire()
            print('FINISHING>>>>>>>>>>>>>>>>>>>>')
            plock.release()
            break
        lock.release()

        semaphore.acquire()
        plock.acquire()
        print('Starting thread')
        plock.release()
        threading.Thread(target=downloadOne).start()
        semaphore.release()

# for i in [threading.Thread(target=downloadOne) for t in range(0, MAX_THREADS)]:
#     i.start()

threading.Thread(target=monitor_threads).start()

out.close()
f.close()
imgs.close()
