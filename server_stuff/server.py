from flask import Flask
from flask import jsonify
from flask import request
from transformers import FIFOAdapter
from functools import *
from typing import Dict
import base64
import threading
import sys

IO_adapter = FIFOAdapter.FIFOAdapter()


'''
fs.open('/home/jeff/Workspace/MultiLevelSoftmax/outpipe', 'r', (err, file) => {
		if(err) {
			console.log(err);

			return fs.close(file, (err, done) =>
			{
				readPipe();
			});
		}

		fs.readFile(file, (err, content) => {
			// TODO: It is possible that given tiny images the pipe may contain multiple classifications. Deal with this later
			if(err)
				console.log(err)

			const contentString = content.toString('utf-8');
			const splitted = contentString.split(",");
			// (leaf_prob, leaf, dijkstra_prob, dijkstra_node, dijkstra_lvl, index, img_data, _, name, prob, name, prob, name, prob, name, prob, name, prob)

            const index = splitted[5];
            splitted[splitted.length - 1] = splitted[splitted.length - 1].replace('>>>EOF<<<', '');

            if(awaitings[index]) {
                awaitings[index](splitted);
                delete awaitings[index];
            } else {
			    classified[index] = splitted;
            }

            numDequeued += 1;

            readPipe();
		})
'''


# async def scrape_for_input(num, loop, ):
#     file = aiofiles.open('', 'r', encoding='utf-8')
#     async for line in file:
#         data = line.split(',')
#         # (leaf_prob, leaf, dijkstra_prob, dijkstra_node, dijkstra_lvl, index, img_data, _, name, prob, name, prob, name, prob, name, prob, name, prob)
#         index = data[5]
#         data[-1] = data[-1].replace(IO_adapter.EOF_SEPARATOR, '')
#
#         if index in waiting:
#             waiting[index](data)
#             del waiting[index]
#         else:
#             classified[index] = data
#
#         num_dequeued += 1
#
#
#     end_time = loop.time() + 50.0
#     while True:
#         print("Loop: {} Time: {}".format(num, datetime.datetime.now()))
#         if (loop.time() + 1.0) >= end_time:
#             break
#         await StreamReader.readline()
#
#
# loop = asyncio.get_event_loop()
# asyncio.ensure_future(display_date(1, loop))
# # asyncio.ensure_future(display_date(2, loop))
#
# loop.run_forever()


classified_view_template = open('classified_view.html', 'r').read()
upload_view_template = open('upload_view.html', 'r').read()


app = Flask(__name__)

def do_app():
    img_index = 0

    classified = {}
    waiting = {}

    num_enqueued = 0
    num_dequeued = 0
    last_dequeue = 0

    def input_scraper():
        nonlocal num_dequeued

        while True:
            try:
                in_str = IO_adapter.read()
                incoming_classification = in_str.split(',')
                index = incoming_classification[5]

                incoming_classification[-1] = incoming_classification[-1].replace(IO_adapter.EOF_SEPARATOR, '')

                if index in waiting:
                    waiting[index](incoming_classification)
                    del waiting[index]
                else:
                    classified[index] = incoming_classification

                num_dequeued += 1
            except Exception as e:
                print(e, file=sys.stderr)

    threading.Thread(target=input_scraper).start()


    def fill(fillers: Dict[str, str], template: str):
        return reduce(lambda accum, k_v: template.replace('{{' + k_v[0] + '}}', k_v[1]), fillers.items(), template)

    def write_pipe(imgIndex, content, priors=''):
        IO_adapter.write(content + '>>>INDEX<<<' + imgIndex + '|' + priors + IO_adapter.EOF_SEPARATOR)

    @app.route("/waiting/<wait_on_label>")
    def wait_on_classification(wait_on_label):

        def on_available_fn(result):
            nonlocal last_dequeue
            last_dequeue = int(result[5])
            print('now its available')
            return jsonify(result)

        if wait_on_label in classified:
            on_available_fn(classified[wait_on_label])
            print('already available')
            del classified[wait_on_label]
        else:
            waiting[wait_on_label] = on_available_fn

    @app.route("/classify")
    def send_upload_view():
        return upload_view_template

    @app.route('/classify-upload', methods=['POST'])
    def upload():
        nonlocal img_index, num_enqueued, last_dequeue

        json_body = jsonify(request.get_json(force=True, silent=True))

        if 'file' in request.files:
            base64_img = base64.standard_b64decode(request.files['file'].read())
        else:
            base64_img = json_body['image_base64'].split(',')[1]

        write_pipe(img_index, base64_img, json_body['priors'] if 'priors' in json_body else '')

        print(json_body['priors'])

        saved_img_index = img_index

        img_index += 1

        num_enqueued += 1

        queued = num_enqueued - last_dequeue - 1
        time_remaining = queued * 0.85

        return fill({'queued': queued, 'timeRemaining': time_remaining, 'imgIndex': saved_img_index},
                    classified_view_template)

do_app()
if __name__ == "__main__":
    app.run(port=8080)
    pass