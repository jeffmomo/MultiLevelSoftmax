from functools import reduce
from typing import Dict
import base64
import multiprocessing
from pathlib import Path
import queue
from collections import namedtuple
from flask import Flask, send_file, request

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

    @app.route("/waiting/<wait_on_index>")
    def wait_on_classification(wait_on_index):
        try:
            a_result: PredictionResult = from_classifier_queue.get_nowait()
            print(a_result)
            image_index = a_result["image_index"]
            ready_result[image_index] = a_result
        except queue.Empty:
            print("no result this time")

        if wait_on_index in ready_result:
            # Redirect!
            return 'HAS RESULT!!!!'
            pass
        else:
            return "NOT YET READY"


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
        to_classifier_queue.put((image_bytes, priors))
        print("written")

        current_queue_size = 69

        return send_templated(str(Path('views') / 'classified.html'), {
            "queued": current_queue_size,
            "timeRemaining": current_queue_size * 0.85,
            "imgIndex": image_id,
        })
    
    return app
