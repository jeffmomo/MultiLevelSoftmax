import multiprocessing
from functools import partial

from classification_server.server import create_app
from classification_server.saved_model_classifier import (
    SavedModelClassifier,
    PredictionResult,
)

def model_worker(saved_model_dir: str, to_model_queue, from_model_queue):
    model = SavedModelClassifier(saved_model_dir)

    while True:
        image_bytes = to_model_queue.pop()
        result = model.predict(image_bytes)

        from_model_queue.push(result)
# TODO Capture signal to terminate


if __name__ == '__main__':
    to_classifier_queue: multiprocessing.Queue = multiprocessing.Queue()
    from_classifier_queue: multiprocessing.Queue = multiprocessing.Queue()

    worker_process = multiprocessing.Process(target=partial(model_worker, to_classifier_queue, from_classifier_queue))
    worker_process.start()

    flask_app = create_app(to_classifier_queue, from_classifier_queue)
    flask_app.run('0.0.0.0', 8080)
