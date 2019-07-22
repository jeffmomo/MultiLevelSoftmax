FROM continuumio/miniconda3
SHELL ["/bin/bash", "-c"]
WORKDIR /app

COPY assets/ assets

COPY conda_env.yaml conda_env.yaml

RUN conda env create -f conda_env.yaml
ENV PATH /opt/conda/envs/tensorflow/bin:$PATH

COPY classification_server classification_server
COPY transformers transformers
COPY hierarchy hierarchy
COPY run_web_classifier.py run_web_classifier.py

CMD ["python3", "run_web_classifier.py", "--saved_model_dir=assets/saved_model", "--labels_path=assets/labels.txt", "--hierarchy_file_path=assets/hierarchy_file.pkl"]