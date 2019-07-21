from functools import reduce
from typing import Dict
import base64
import multiprocessing
from pathlib import Path
import queue
from collections import namedtuple
from flask import Flask, send_file, request, jsonify

from classification_server.saved_model_classifier import PredictionResult

def fill(fillers: Dict[str, str], template: str):
    return reduce(
        lambda accum, k_v: accum.replace("{{" + k_v[0] + "}}", str(k_v[1])),
        fillers.items(),
        template,
    )


def send_templated(template_path, fillers):
    with open(Path(__file__).parent / template_path) as f:
        template = f.read()

    return fill(fillers, template)


def _get_b64_from_dataurl(b64string):
    return b64string.split(",")[1]


def create_app(to_classifier_queue: queue.Queue, from_classifier_queue: queue.Queue):
    app = Flask(__name__)

    ready_result = {}
    request_metadata = {}

    queue_size_counter = multiprocessing.Value('i')
    queue_size_counter.value = 0

    @app.route("/waiting/<wait_on_index>")
    def wait_on_classification(wait_on_index):
        try:
            result, hierarchy_json, clsf_index = from_classifier_queue.get_nowait()
            print('gotten results for', str(clsf_index))
            ready_result[clsf_index] = (result, hierarchy_json)

            with queue_size_counter.get_lock():
                queue_size_counter.value -= 1
        except queue.Empty:
            print("no result this time")

        # TODO: free up result dict after returning a result
        print(list(ready_result.keys()))
        wait_on_index = int(wait_on_index)
        if wait_on_index in ready_result:
            classification_result, hierarchy_json = ready_result[wait_on_index]
            original_image_bytes, priors = request_metadata[wait_on_index]
            response = jsonify({
                'classifications': hierarchy_json,
                'saliency_image': classification_result.saliency,
                'original_image': str(base64.b64encode(original_image), 'utf8'),
                'priors': priors,
            })

            del ready_result[wait_on_index]
            del request_metadata[wait_on_index]

            return response
        else:
            return jsonify({
                'in_progress': True
            })


    @app.route("/classify")
    def send_upload_view():
        return send_file(Path("views") / "upload_advanced.html")


    @app.route("/classify-mobile")
    def send_upload_mobile_view():
        return send_file(Path("views") / "upload.html")


    @app.route("/classify-upload", methods=["POST"])
    def upload():
        form_dict = request.form.to_dict()
        priors = form_dict.get("priors")

        if "example" in request.files:
            image_bytes = request.files["example"].read()
        else:
            image_bytes = base64.b64decode(_get_b64_from_dataurl(form_dict["image_base64"]))

        image_id = id(image_bytes)

        print(str(base64.b64encode(image_bytes), 'utf8'))
        to_classifier_queue.put((image_bytes, priors, image_id))

        request_metadata[image_id] = image_bytes, priors

        print("written")

        with queue_size_counter.get_lock():
            current_queue_size = queue_size_counter.value
            queue_size_counter.value += 1

        return send_templated(str(Path('views') / 'classified.html'), {
            "queued": current_queue_size,
            "timeRemaining": current_queue_size * 0.85 + 4,
            "imgIndex": image_id,
        })
    
    return app
