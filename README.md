# MultiLevelSoftmax

All the necessary assets to run the web classifier are included in the repo. 

Note that by default this runs the classifier only on the CPU

## Getting set up 

### Option 1 - Locally
Tensorflow and the web server have quite a few dependencies. These dependencies have been forzen into a conda environment file. 
To recreate the environment, simply install Conda and then:  
```
conda env create -f conda_env.yaml
conda activate tensorflow
```

Since assets are all here, we run the classifier as follows:  
```
python3 run_web_classifier.py \
--saved_model_dir=assets/saved_model \
--labels_path=assets/labels.txt \
--hierarchy_file_path=assets/hierarchy_file.pkl
```

### Option 2 - Docker
First make sure Docker is installed and running

To run it:
```
docker build -t species_classifier .
docker run --rm -p 8000:8000 species_classifier
```


The web server will be available on 
```
localhost:8000/classify
```
