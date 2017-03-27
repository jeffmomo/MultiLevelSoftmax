import os
import sys

class FIFOAdapter:

    EOF_SEPARATOR = '>>>EOF<<<'
    INDEX_SEPARATOR = '>>>INDEX<<<'

    def __init__(self, to_server_resource=None, to_classifier_resource=None):

        if to_server_resource is None:
            to_server_resource = './in_pipe'
            try:
                os.mkfifo(to_server_resource)
            except Exception as e:
                print(str(e), file=sys.stderr)

        if to_classifier_resource is None:
            to_classifier_resource = './out_pipe'
            try:
                os.mkfifo(to_classifier_resource)
            except Exception as e:
                print(str(e), file=sys.stderr)

        self.in_resource = to_server_resource
        self.out_resource = to_classifier_resource

        # do init stuff
        pass

    def setup(self):

        pass

    def write(self, content):
        outpipe = open(self.out_resource, 'w')
        outpipe.write(content + '>>>EOF<<<')
        outpipe.close()


    def read(self):
        return open(self.in_resource, 'r', encoding='utf-8').read()
        pass


