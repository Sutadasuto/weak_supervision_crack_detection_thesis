# Weakly supervised crack detection (using U-VGG19 as backbone)
Code used to produce the results presented in my PhD thesis (Chapter 3). It is an extension of the work presented in:

```
@article{neurocomputing,
    title = {Pixel-accurate road crack detection in presence of inaccurate annotations},
    journal = {Neurocomputing},
    volume = {480},
    pages = {1-13},
    year = {2022},
    issn = {0925-2312},
    doi = {https://doi.org/10.1016/j.neucom.2022.01.051},
    url = {https://www.sciencedirect.com/science/article/pii/S0925231222000728},
    author = {Rodrigo Rill-García and Eva Dokladalova and Petr Dokládal},
}
```

If using this version of the code, or the version for the journal paper (available at https://github.com/Sutadasuto/weak_supervision_crack_detection), kindly cite the paper above.

The code and documentation intended to use U-VGG19 as a pure supervised approach is available at: https://github.com/Sutadasuto/uvgg19_crack_detection
The code and documentation for Syncrack is available at: https://github.com/Sutadasuto/syncrack_generator

## Pre-requisites
This repository was tested on two setups:
* Ubuntu 18.04 with a Nvidia GeForce GTX 1050 using Driver Version 440.82 and CUDA Version 10.2
* Ubuntu 20.04 with a Nvidia GeForce RTX 2070 using Driver Version 450.80.02 and CUDA Version 11.0

The network was build using Tensorflow 2.1.0. An environment.yml is provided in this repository to clone the environment used (recommended).

## Get pseudo-labels
### For self-training
The self-training approach requires to first train a model. You can train a fresh version of U-VGG19 using the script "train_and_validate.py" (see the link provided at the beginning of the document for more information). Once the model is trained, it is used to predict new pseudo-labels. You can re-run the same script, using 0 epochs and assigning the learned weights from the previous training (see the link for more information).

### For majority/consensus voting
This ensemble approach requires to train a set of weak learners. You can train these learners as described in the paper by running the "train_for_bagging.py" script.The input parameters are basically the same as those of "train_and_validate.py", but you can choose 'k' (the number of learners) by providing the '-k' argument. The folder generated by this script then can be used to generate the pseudo-labels.

To do this, you must run the "bagging_voting.py" script. Additionally to the model and datasets, it will require you to provide the path to the folder generated by the previous script (using the '-w' argument). You can provide the voting strategy too ('majority' or 'consensus', through the '-s' argument).

The resulting pseudo-labels will be saved in a new folder in the project's root.

### For k-NN voting
This approach requires again to have a trained model. Once you have learned weights, you can obtain pseudo-labels from the network using a k-NN approach. To do this, run the "knn_with_prob_maps.py" script. As usual, you'll be required to provide the dataset, model and weights as arguments. You can also provide the value for k, using the '-k' argument.

The new pseudo-labels will be saved in a new folder inside the project's root.

## Training with pseudo-labels

### Relabeling
For this, you need to replace the gt annotations in your dataset folders and train a model normally.

### Removing
This requires to weight pixels during training. This has been already implemented: simply run the "train_and_validate_with_weights.py" script. Unlike "train_and_validate.py", this script requires you 2 paths per dataset: the one with raw labels, and the one with pseudo-labels. Pseudo-labels path is provided through the '-pc' argument.

## Validate on clean data
You can always validate a pre-trained model on any desired dataset by using "validate.py". When using "train_and_validate.py", you can provide '--save_validation_paths' as 'True' to obtain a text file containing the paths of the images used as validation split (so that you always validate on the same paths).

## Analyze annotated cracks pixel-intensities
You can measure the mean and standard deviation (per image) of the gray-scale pixels annotated as crack. This is done by running the "validate_model_intensities_on_dataset.py" script. The results are saved to a csv file in the project's root folder.
