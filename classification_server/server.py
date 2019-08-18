import base64
import multiprocessing
import queue
import time
from collections import namedtuple
from functools import reduce
from pathlib import Path
from typing import Any, Dict
import pickle
import os
import threading
import logging

from misc.utils import time_it
from classification_server.saved_model_classifier import PredictionResult
from flask import Flask, jsonify, request, send_file, send_from_directory

_OVERLOAD_THRESHOLD = 20

logging.basicConfig()
logger = logging.getLogger(__name__)

# Store done classifications that are awaiting poll
ready_result: Dict[int, tuple] = {}
request_metadata: Dict[int, tuple] = {}

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


def schedule_garbage_collection(action, delay_seconds=20):
    def gc():
        time.sleep(delay_seconds)
        try:
            action()
        except Exception:
            logger.exception(f'Failed to remove during garbage collection')
    
    threading.Thread(target=gc).start()


def create_app(to_classifier_queue: queue.Queue, from_classifier_queue: queue.Queue, queue_size_counter: multiprocessing.Value):
    app = Flask(__name__)

    @app.route("/assets/<filename>")
    def send_assets(filename):
        return send_from_directory("3rdparty", filename)

    @app.route("/waiting/<wait_on_index>")
    def wait_on_classification(wait_on_index):
        wait_on_index = int(wait_on_index)

        # On every poll, try to dequeue a done classification
        try:
            result, hierarchy_json, clsf_index = from_classifier_queue.get_nowait()

            ready_result[clsf_index] = (result, hierarchy_json)

            def cleanup():
                del ready_result[clsf_index]

            schedule_garbage_collection(cleanup, 5)

        except queue.Empty:
            pass

        # If this ID is done, then we return result
        if wait_on_index in ready_result:
            classification_result, hierarchy_json = ready_result[wait_on_index]
            original_image_bytes, priors = request_metadata[wait_on_index]
            response = jsonify({
                'classifications': hierarchy_json,
                'saliency_image': classification_result.saliency,
                'original_image': str(base64.b64encode(original_image_bytes), 'utf8'),
                'priors': priors,
            })

            del ready_result[wait_on_index]
            del request_metadata[wait_on_index]

            return response
        else:
            # Otherwise tell it to keep polling
            return jsonify({
                'in_progress': True
            })

    @app.route("/")
    @app.route("/classify")
    def send_upload_view():
        return send_file(Path("views") / "upload_advanced.html")


    @app.route("/classify-mobile")
    def send_upload_mobile_view():
        return send_file(Path("views") / "upload.html")


    @app.route("/classify-upload", methods=["POST"])
    def upload():
        # Check if queue is too deep (i.e. server is overloaded)
        # If so, send denied page
        if queue_size_counter.value > _OVERLOAD_THRESHOLD:
            return send_templated(Path('views') / 'denied.html', {
                'queued': str(queue_size_counter.value),
                'timeRemaining': '%.2f seconds' % (queue_size_counter.value * 6 + 4, ),
            })

        form_dict = request.form.to_dict()
        priors = form_dict.get("priors", '')

        # Expects 2 formats, depending on whether darkroom.js is used or not (i.e. classify-advanced) 
        with time_it('deserialise_request'):
            if "example" in request.files:
                image_bytes = request.files["example"].read()
            else:
                image_bytes = base64.b64decode(_get_b64_from_dataurl(form_dict["image_base64"]))

        # Assign a unique ID to the request
        image_id = id(image_bytes)

        with time_it('put_queue'):
            to_classifier_queue.put((image_bytes, priors, image_id))

        # Store some metadata here for this particular request ID
        request_metadata[image_id] = image_bytes, priors
        def cleanup():
            del request_metadata[image_id]
        
        schedule_garbage_collection(cleanup, 20)

        with queue_size_counter.get_lock():
            queue_size_counter.value += 1
            current_queue_size = queue_size_counter.value

        return send_templated(str(Path('views') / 'classified.html'), {
            "queued": current_queue_size,
            "timeRemaining": current_queue_size * 10 + 2,
            "imgIndex": image_id,
        })
    
    return app
