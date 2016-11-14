import os
import threading

try:
    os.mkfifo('./pipe')
except Exception as e:
    print(e)

# writes to piperino
def writer():
    while True:
        f = open('./pipe', 'w')
        f.write('3' + '>>>EOF<<<')
        f.close()

threading.Thread(target=writer).start()

