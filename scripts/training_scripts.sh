# To create the training dataset, have a folder of folders whose name is the classes, with each folder containing images of that class. 
# Then run this script
python convert_data_folder --train_dir <training_directory> [--output_directory <output_dir>] [--validation_num <number of images in validation>]

# Run this for help
python convert_data_folder --help




# To train the standard classifier
python train_image_classifier.py --train_dir=/home/jeff/Workspace/tmp/species_big_restored_train \
--dataset_dir=/media/jeff/9566f510-ddf5-468b-a0fb-1d10bd7fabca/data_dir --dataset_split_name=train \
--batch_size=32 --optimizer=adam --save_summaries_secs=300 --model_name=inception_resnet_v2 \
--dataset_name=species_big --preprocessing_name=species_big \
--checkpoint_path=/home/jeff/Workspace/tmp/checkpoints/inception_resnet_v2_2016_08_30.ckpt \
--checkpoint_exclude_scopes=InceptionResnetV2/Logits,InceptionResnetV2/AuxLogits/Logits

# To train the multiview classifier
python specialised_train_multiview.py --train_dir=/home/jeff/Workspace/tmp/species_multiview \
--dataset_dir=/media/jeff/9566f510-ddf5-468b-a0fb-1d10bd7fabca/data_dir --dataset_split_name=train \
--batch_size=16 --optimizer=adam \
--checkpoint_path=/home/jeff/Workspace/tmp/checkpoints/inception_resnet_v2_2016_08_30.ckpt \
--checkpoint_exclude_scopes=InceptionResnetV2/Logits,InceptionResnetV2/AuxLogits/Logits,InceptionResnetV2/Side,InceptionResnetV2/Concat \
--save_summaries_secs=300 --learning_rate=0.1


python3 specialised_train_multiview.py --train_dir=/home/jeff/Workspace/tmp/species_multiview_multistage \
--dataset_dir=/media/jeff/9566f510-ddf5-468b-a0fb-1d10bd7fabca/data_dir --dataset_split_name=train \
--batch_size=16 --optimizer=adam \
--checkpoint_path=/home/jeff/Workspace/tmp/checkpoints/inception_resnet_v2_2016_08_30.ckpt \
--checkpoint_exclude_scopes=InceptionResnetV2/Logits,InceptionResnetV2/AuxLogits/Logits,InceptionResnetV2/Side,InceptionResnetV2/Concat \
--save_summaries_secs=600 --schedule=complete_schedule --native_indices=False
