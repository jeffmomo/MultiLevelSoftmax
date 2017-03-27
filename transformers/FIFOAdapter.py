import os
import sys

class FIFOAdapter:

    EOF_SEPARATOR = '>>>EOF<<<'
    INDEX_SEPARATOR = '>>>INDEX<<<'

    def __init__(self, in_resource=None, out_resource=None):

        if in_resource is None:
            in_resource = './in_pipe'
            try:
                os.mkfifo(in_resource)
            except Exception as e:
                print(str(e), file=sys.stderr)

        if out_resource is None:
            out_resource = './out_pipe'
            try:
                os.mkfifo(out_resource)
            except Exception as e:
                print(str(e), file=sys.stderr)

        self.in_resource = in_resource
        self.out_resource = out_resource

        # do init stuff
        pass

    def setup(self):

        pass

    def write(self, content):
        print('about to write...' + content)
        outpipe = open(self.out_resource, 'w', buffering=0)
        outpipe.write(content + '>>>EOF<<<')
        outpipe.close()


    def read(self):
        return open(self.in_resource, 'r', encoding='utf-8').read()
        pass


