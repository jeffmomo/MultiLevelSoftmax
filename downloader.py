import threading
import time

uri_list = [str(x) for x in range(100, 1000)]

counter = 0
lock = threading.Lock()
plock = threading.Lock()


def downloadOne():
    while True:
        lock.acquire()
        if not len(uri_list):
            break
        uri = uri_list.pop()
        lock.release()
        time.sleep(1)
        plock.acquire()
        print(uri)
        plock.release()

    lock.release()


# t = threading.Thread(target=downloadOne)


for i in [threading.Thread(target=downloadOne) for t in range(0, 10)]:
    i.start()

# t.start()
