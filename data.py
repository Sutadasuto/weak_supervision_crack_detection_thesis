import cv2
import importlib
import numpy as np
import random
import scipy.io
import subprocess
import os

from scores import calculate_confusion_matrix, calculate_PRF

from math import ceil
from tensorflow.keras.preprocessing import image


### Getting image paths
def create_image_paths(dataset_names, dataset_paths):
    paths = np.array([[], []], dtype=np.str)
    for idx, dataset in enumerate(dataset_names):
        dataset_name = dataset
        dataset_path = dataset_paths[idx]
        if dataset_name == "cfd" or dataset_name == "cfd-pruned" or dataset_name == "cfd-corrected":
            or_im_paths, gt_paths = paths_generator_cfd(dataset_path)
        elif dataset_name == "aigle-rn":
            or_im_paths, gt_paths = paths_generator_crack_dataset(dataset_path, "AIGLE_RN")
        elif dataset_name == "esar":
            or_im_paths, gt_paths = paths_generator_crack_dataset(dataset_path, "ESAR")
        elif dataset_name == "crack500" or dataset_name == "gaps384" or dataset_name == "cracktree200":
            or_im_paths, gt_paths = paths_generator_fphb(dataset_path, dataset_name)
        elif dataset_name == "syncrack":
            or_im_paths, gt_paths = paths_generator_syncrack(dataset_path)
        elif dataset_name == "concrete":
            or_im_paths, gt_paths = paths_generator_concrete(dataset_path)
        elif dataset_name == "text":
            or_im_paths, gt_paths = paths_generator_from_text(dataset_path)

        paths = np.concatenate([paths, [or_im_paths, gt_paths]], axis=-1)
    return paths


def paths_generator_crack_dataset(dataset_path, subset):
    ground_truth_path = os.path.join(dataset_path, "TITS", "GROUND_TRUTH", subset)
    training_data_path = os.path.join(dataset_path, "TITS", "IMAGES", subset)
    images_path, dataset = os.path.split(training_data_path)
    if dataset == "ESAR":
        file_end = ".jpg"
    elif dataset == "AIGLE_RN":
        file_end = "or.png"

    ground_truth_image_paths = sorted([os.path.join(ground_truth_path, f) for f in os.listdir(ground_truth_path)
                                       if not f.startswith(".") and (f.endswith(".png") or f.endswith(".jpg"))],
                                      key=lambda f: f.lower())

    training_image_paths = [os.path.join(training_data_path, "Im_" + os.path.split(f)[-1].replace(".png", file_end)) for
                            f in ground_truth_image_paths]

    return training_image_paths, ground_truth_image_paths


def paths_generator_cfd(dataset_path):
    ground_truth_path = os.path.join(dataset_path, "groundTruthPng")

    if not os.path.exists(ground_truth_path):
        os.makedirs(ground_truth_path)

        ground_truth_image_paths = sorted(
            [os.path.join(dataset_path, "groundTruth", f) for f in os.listdir(os.path.join(dataset_path, "groundTruth"))
             if not f.startswith(".") and f.endswith(".mat")],
            key=lambda f: f.lower())
        for idx, path in enumerate(ground_truth_image_paths):
            mat = scipy.io.loadmat(path)
            img = (mat["groundTruth"][0][0][0] - 1).astype(np.float32)
            cv2.imwrite(path.replace("groundTruth", "groundTruthPng").replace(".mat", ".png"), 255 * img)

    ground_truth_image_paths = sorted([os.path.join(ground_truth_path, f) for f in os.listdir(ground_truth_path)
                                       if not f.startswith(".") and f.endswith(".png")],
                                      key=lambda f: f.lower())

    training_image_paths = [os.path.join(dataset_path, "image", os.path.split(f)[-1].replace(".png", ".jpg")) for f in
                            ground_truth_image_paths]

    return training_image_paths, ground_truth_image_paths


def paths_generator_fphb(dataset_path, dataset_name):
    if dataset_name == "crack500":
        ground_truth_paths = [os.path.join(dataset_path, "traincrop"), os.path.join(dataset_path, "valcrop"),
                              os.path.join(dataset_path, "testcrop")]
        ground_truth_image_paths = []
        for ground_truth_path in ground_truth_paths:
            ground_truth_image_paths += sorted(
                [os.path.join(ground_truth_path, f) for f in os.listdir(ground_truth_path)
                 if not f.startswith(".") and f.endswith(".png")],
                key=lambda f: f.lower())

        training_image_paths = [f.replace(".png", ".jpg") for f in ground_truth_image_paths]

    elif dataset_name == "gaps384":
        ground_truth_path = os.path.join(dataset_path, "croppedgt")
        image_path = os.path.join(dataset_path, "croppedimg")

        ground_truth_image_paths = sorted([os.path.join(ground_truth_path, f) for f in os.listdir(ground_truth_path)
                                           if not f.startswith(".") and f.endswith(".png")],
                                          key=lambda f: f.lower())
        training_image_paths = sorted([os.path.join(image_path, f.replace(".png", ".jpg"))
                                       for f in os.listdir(ground_truth_path)
                                       if not f.startswith(".") and f.endswith(".png")],
                                      key=lambda f: f.lower())

    elif dataset_name == "cracktree200":
        ground_truth_path = os.path.join(dataset_path, "cracktree200_gt")
        image_path = os.path.join(dataset_path, "cracktree200rgb")

        ground_truth_image_paths = sorted([os.path.join(ground_truth_path, f) for f in os.listdir(ground_truth_path)
                                           if not f.startswith(".") and f.endswith(".png")],
                                          key=lambda f: f.lower())
        training_image_paths = sorted([os.path.join(image_path, f.replace(".png", ".jpg"))
                                       for f in os.listdir(ground_truth_path)
                                       if not f.startswith(".") and f.endswith(".png")],
                                      key=lambda f: f.lower())

    return training_image_paths, ground_truth_image_paths


def paths_generator_syncrack(dataset_path):
    ground_truth_image_paths = sorted([os.path.join(dataset_path, f) for f in os.listdir(dataset_path)
                                       if not f.startswith(".") and f.endswith("_gt.png")], key=lambda f: f.lower())

    training_image_paths = [os.path.join(dataset_path, os.path.split(f)[1].replace("_gt.png", ".jpg")) for
                            f in ground_truth_image_paths]

    return training_image_paths, ground_truth_image_paths


def paths_generator_from_text(text_file_path):
    with open(text_file_path, "r") as file:
        lines = file.readlines()
    paths_array = np.concatenate([np.array([line.strip().split(";")]) for line in lines], axis=0)
    return paths_array[:, 0], paths_array[:, 1]


def paths_generator_concrete(dataset_path):
    ground_truth_image_paths = sorted([os.path.join(dataset_path, f) for f in os.listdir(dataset_path)
                                       if not f.startswith(".") and f.endswith("_gt.png")], key=lambda f: f.lower())
    base_name = os.path.split(ground_truth_image_paths[0])[-1].replace("_gt.png", "")
    for f in os.listdir(dataset_path):
        if f.startswith(base_name) and not f.endswith("_gt.png"):
            extension = os.path.splitext(f)[-1]
            break

    training_image_paths = [os.path.join(dataset_path, os.path.split(f)[1].replace("_gt.png", extension)) for
                            f in ground_truth_image_paths]

    return training_image_paths, ground_truth_image_paths


def paths_generator_from_text(text_file_path):
    with open(text_file_path, "r") as file:
        lines = file.readlines()
    paths_array = np.concatenate([np.array([line.strip().split(";")]) for line in lines], axis=0)
    return paths_array[:, 0], paths_array[:, 1]


### Loading images for Keras

# Utilities
def manual_padding(image, n_pooling_layers):
    # Assuming N pooling layers of size 2x2 with pool size stride (like in U-net and multiscale U-net), we add the
    # necessary number of rows and columns to have an image fully compatible with up sampling layers.
    divisor = 2 ** n_pooling_layers
    try:
        h, w = image.shape
    except ValueError:
        h, w, c = image.shape
    new_h = divisor * ceil(h / divisor)
    new_w = divisor * ceil(w / divisor)
    if new_h == h and new_w == w:
        return image

    if new_h != h:
        new_rows = np.flip(image[h - new_h:, :, ...], axis=0)
        image = np.concatenate([image, new_rows], axis=0)
    if new_w != w:
        new_cols = np.flip(image[:, w - new_w:, ...], axis=1)
        image = np.concatenate([image, new_cols], axis=1)
    return image


def flipped_version(image, flip_typ):
    if flip_typ is None:
        return image
    elif flip_typ == "h":
        return np.fliplr(image)
    elif flip_typ == "v":
        return np.flipud(image)


def noisy_version(image, noise_typ):
    int_type = True if image.dtype == np.uint8 else False
    if noise_typ == "gauss":
        row, col, ch = image.shape
        mean = 0
        var = 0.1 * image.max()
        sigma = var ** 0.5
        gauss = np.random.normal(mean, sigma, (row, col, ch))
        gauss = gauss.reshape(row, col, ch)
        noisy = image + gauss
        return noisy if not int_type else noisy.astype(np.uint8)

    elif noise_typ == "s&p":
        s_vs_p = 0.5
        amount = 0.004
        out = np.copy(image)
        # Salt mode
        num_salt = int(np.ceil(amount * image.size * s_vs_p))
        coords = [np.random.randint(0, i - 1, num_salt)
                  for i in image.shape[:-1]]
        for channel in range(image.shape[-1]):
            channel_coords = tuple(coords + [np.array([channel for i in range(num_salt)])])
            out[channel_coords] = image.max()

        # Pepper mode
        num_pepper = int(np.ceil(amount * image.size * (1. - s_vs_p)))
        coords = [np.random.randint(0, i - 1, num_pepper)
                  for i in image.shape[:-1]]
        for channel in range(image.shape[-1]):
            channel_coords = tuple(coords + [np.array([channel for i in range(num_pepper)])])
            out[channel_coords] = image.min()
        return out if not int_type else out.astype(np.uint8)

    elif noise_typ == "speckle":
        row, col, ch = image.shape
        gauss = np.random.randn(row, col, ch) / 4.0
        noisy = image + image * gauss
        return noisy if not int_type else noisy.astype(np.uint8)

    elif noise_typ is None:
        return image


def illumination_adjustment_version(image, alpha, beta):
    image = alpha * image
    if beta == "bright":
        shift = 255 - np.max(image)
    elif beta == "dark":
        shift = -np.min(image)
    else:
        shift = 0
    return np.clip(image + shift, 0, 255).astype(np.uint8)


# The version with the previous data augmentation strategy. The one used in the paper (without data augmentation)
def illumination_adjustment_version_legacy(image, alpha, beta):
    if image.dtype == np.uint8:
        return np.clip(alpha * (image + beta), 0, 255)
    return np.clip(alpha * (image + beta), 0.0, 1.0)


def rotated_version(image, angle):
    if angle is None:
        return image

    k = int(angle / 90)
    return np.rot90(image, k)


def get_corners(im, input_size):
    h, w, c = im.shape
    rows = h / input_size[0]
    cols = w / input_size[0]

    corners = []
    for i in range(ceil(rows)):
        for j in range(ceil(cols)):
            if i + 1 <= rows:
                y = i * input_size[0]
            else:
                y = h - input_size[0]

            if j + 1 <= cols:
                x = j * input_size[1]
            else:
                x = w - input_size[1]

            corners.append([y, x])
    return corners


def crop_generator(im, gt, input_size):
    corners = get_corners(im, input_size)
    for corner in corners:
        x = im[corner[0]:corner[0] + input_size[0], corner[1]:corner[1] + input_size[1], ...]
        y = gt[corner[0]:corner[0] + input_size[0], corner[1]:corner[1] + input_size[1], ...]
        yield [x, y]


# A generator, creating all the possible combined augmented data for a single input pair
def augmentation(im, gt, **kwargs):
    noises = kwargs["noises"]
    alphas = kwargs["alphas"]
    betas = kwargs["betas"]
    flips = kwargs["flips"]
    zooms = kwargs["zooms"]
    rot_angs = kwargs["rot_angs"]
    shear_angs = kwargs["shear_angs"]

    for noise in noises:
        noisy = noisy_version(im, noise)

        for alpha in alphas:
            for beta in betas:
                adjusted = illumination_adjustment_version(noisy, alpha, beta)

                for flip in flips:
                    flipped = flipped_version(adjusted, flip)
                    flipped_gt = flipped_version(gt, flip)

                    for zoom in zooms:
                        for rot_ang in rot_angs:
                            for shear_ang in shear_angs:
                                affine_transformed = image.apply_affine_transform(flipped, rot_ang, shear=shear_ang,
                                                                                  zx=zoom, zy=zoom, fill_mode="reflect")
                                affine_transformed_gt = image.apply_affine_transform(flipped_gt, rot_ang,
                                                                                     shear=shear_ang, zx=zoom, zy=zoom,
                                                                                     fill_mode="reflect")
                                yield [affine_transformed, np.where(affine_transformed_gt > 0.5, 1.0, 0.0)]


# Apply a random transformation to an input pair
def random_transformation(im, gt, **kwargs):
    noise = random.choice(kwargs["noises"])
    alpha = random.choice(kwargs["alphas"])
    beta = random.choice(kwargs["betas"])
    flip = random.choice(kwargs["flips"])
    zoom = random.choice(kwargs["zooms"])
    rot_ang = random.choice(kwargs["rot_angs"])
    shear_ang = random.choice(kwargs["shear_angs"])

    noisy = noisy_version(im, noise)
    adjusted = illumination_adjustment_version(noisy, alpha, beta)

    flipped = flipped_version(adjusted, flip)
    flipped_gt = flipped_version(gt, flip)

    affine_transformed = image.apply_affine_transform(flipped, rot_ang, shear=shear_ang, zx=zoom, zy=zoom,
                                                      fill_mode="reflect")
    affine_transformed_gt = image.apply_affine_transform(flipped_gt, rot_ang, shear=shear_ang, zx=zoom, zy=zoom,
                                                         fill_mode="reflect")

    return affine_transformed, np.where(affine_transformed_gt > 0.5, 1.0, 0.0)


# Image generators
def get_image(im_path):
    im = cv2.cvtColor(cv2.imread(im_path), cv2.COLOR_BGR2RGB)

    im = manual_padding(im, n_pooling_layers=4)
    if len(im.shape) == 2:
        im = im[..., None]  # Channels last
    return im


def get_gt_image(gt_path):
    gt = cv2.imread(gt_path, cv2.IMREAD_GRAYSCALE)
    binary = True if len(np.unique(gt)) <= 2 else False
    gt = (gt / 255.0)
    if binary:
        n_white = np.sum(gt)
        n_black = gt.shape[0] * gt.shape[1] - n_white
        if n_black < n_white:
            gt = 1 - gt

    gt = manual_padding(gt, n_pooling_layers=4)
    if len(gt.shape) < 3:
        return gt[..., None]  # Channels last
    else:
        return gt


def validation_image_generator(paths, batch_size=1, rgb_preprocessor=None):
    _, n_images = paths.shape
    rgb = True if rgb_preprocessor else False
    i = 0
    while True:
        batch_x = []
        batch_y = []
        b = 0
        while b < batch_size:
            if i == n_images:
                i = 0
            im_path = paths[0][i]
            gt_path = paths[1][i]

            im = get_image(im_path)
            gt = get_gt_image(gt_path)
            if rgb:
                batch_x.append(rgb_preprocessor(im))
            else:
                batch_x.append(im)
            batch_y.append(gt)
            b += 1
            i += 1

        yield np.array(batch_x), np.array(batch_y)


# This version applies a random transformation to each input pair before feeding it to the model
def train_image_generator(paths, input_size, batch_size=1, count_samples_mode=False,
                          rgb_preprocessor=None, data_augmentation=True):
    _, n_images = paths.shape
    rgb = True if rgb_preprocessor else False

    # All available transformations for data augmentation
    if data_augmentation:
        augmentation_params = {
            "noises": [None, "gauss", "s&p"],
            "alphas": [1.0, 0.8],  # Simple contrast control
            "betas": [None, "bright", "dark"],  # Simple brightness control
            "flips": [None, "h", "v"],  # Horizontal, Vertical
            "zooms": [1.0, 2.0, 1.5],  # Zoom rate in both axis; >1.0 zooms out
            "rot_angs": [i * 5.0 for i in range(int(90.0 / 5.0 + 1))],  # Rotation angle in degrees
            "shear_angs": [i * 5.0 for i in range(int(45.0 / 5.0 + 1))]  # Shear angle in degrees
        }

    # This means no noise, no illumination adjustment, no rotation and no flip (i.e. only the original image is
    # provided)
    else:
        augmentation_params = {
            "noises": [None],  # s&p = salt and pepper
            "alphas": [1.0],  # Simple contrast control
            "betas": [None],  # Simple brightness control
            "flips": [None],  # Horizontal, Vertical
            "zooms": [1.0],  # Zoom rate in both axis; >1.0 zooms out
            "rot_angs": [0.0],  # Degrees
            "shear_angs": [0.0],  # Degrees
        }

    i = -1
    prev_im = False
    n_samples = 0

    while True:
        batch_x = []
        batch_y = []
        b = 0
        while b < batch_size:

            if not prev_im:
                i += 1

                if i == n_images:
                    if count_samples_mode:
                        yield n_samples
                    i = 0
                    np.random.shuffle(paths.transpose())

                if count_samples_mode:
                    print("\r%s/%s paths analyzed so far" % (str(i + 1).zfill(len(str(n_images))), n_images), end='')

                im_path = paths[0][i]
                gt_path = paths[1][i]

                or_im = get_image(im_path)
                or_gt = get_gt_image(gt_path)

            if input_size:
                if not prev_im:
                    win_gen = crop_generator(or_im, or_gt, input_size)
                    prev_im = True
                try:
                    [im, gt] = next(win_gen)
                except StopIteration:
                    prev_im = False
                    continue

                x, y = random_transformation(im, gt, **augmentation_params)

                x = manual_padding(x, 4)
                y = manual_padding(y, 4)
                if rgb:
                    batch_x.append(rgb_preprocessor(x))
                else:
                    batch_x.append(x)
                batch_y.append(y)
                n_samples += 1
                b += 1

            else:
                im, gt = random_transformation(or_im, or_gt, **augmentation_params)
                im = manual_padding(im, 4)
                if rgb:
                    batch_x.append(rgb_preprocessor(im))
                else:
                    batch_x.append(im)
                gt = manual_padding(gt, 4)
                batch_y.append(gt)
                n_samples += 1
                b += 1

        if not count_samples_mode:
            yield np.array(batch_x), np.array(batch_y)


# This version creates all the available transformations of an input pair during each epoch
def train_image_generator_exhaustive(paths, input_size, batch_size=1, count_samples_mode=False,
                                     rgb_preprocessor=None, data_augmentation=True):
    _, n_images = paths.shape
    rgb = True if rgb_preprocessor else False

    # All available transformations for data augmentation
    if data_augmentation:
        augmentation_params = {
            "noises": [None, "gauss"],
            "alphas": [1.0, 0.8],  # Simple contrast control
            "betas": [None, "bright", "dark"],  # Simple brightness control
            "flips": [None, "h", "v"],  # Horizontal, Vertical
            "zooms": [1.0, 2.0, 1.5],  # Zoom rate in both axis; >1.0 zooms out
            "rot_angs": [0.0, 45.0, 90.0],  # Rotation angle in degrees
            "shear_angs": [0.0, 45.0]  # Shear angle in degrees
        }

    # This means no noise, no illumination adjustment, no rotation and no flip (i.e. only the original image is
    # provided)
    else:
        augmentation_params = {
            "noises": [None],  # s&p = salt and pepper
            "alphas": [1.0],  # Simple contrast control
            "betas": [None],  # Simple brightness control
            "flips": [None],  # Horizontal, Vertical
            "zooms": [1.0],  # Zoom rate in both axis; >1.0 zooms out
            "rot_angs": [0.0],  # Degrees
            "shear_angs": [0.0],  # Degrees
        }

    i = -1
    prev_im = False
    prev_crop = False
    n_samples = 0

    while True:
        batch_x = []
        batch_y = []
        b = 0
        while b < batch_size:

            if not prev_im:
                i += 1

                if i == n_images:
                    if count_samples_mode:
                        yield n_samples
                    i = 0
                    np.random.shuffle(paths.transpose())

                if count_samples_mode:
                    print("\r%s/%s paths analyzed so far" % (str(i + 1).zfill(len(str(n_images))), n_images), end='')

                im_path = paths[0][i]
                gt_path = paths[1][i]

                or_im = get_image(im_path)
                or_gt = get_gt_image(gt_path)

            if input_size:
                if not prev_im:
                    win_gen = crop_generator(or_im, or_gt, input_size)
                    prev_im = True
                try:
                    if not prev_crop:
                        [im, gt] = next(win_gen)
                except StopIteration:
                    prev_im = False
                    continue

                if not prev_crop:
                    aug_gen = augmentation(im, gt, **augmentation_params)
                    prev_crop = True
                try:
                    [x, y] = next(aug_gen)
                except StopIteration:
                    prev_crop = False
                    continue

                x = manual_padding(x, 4)
                y = manual_padding(y, 4)
                if rgb:
                    batch_x.append(rgb_preprocessor(x))
                else:
                    batch_x.append(x)
                batch_y.append(y)
                n_samples += 1
                b += 1

            else:
                if not prev_im:
                    aug_gen = augmentation(or_im, or_gt, **augmentation_params)
                    prev_im = True
                try:
                    [im, gt] = next(aug_gen)
                except StopIteration:
                    prev_im = False
                    continue

                im = manual_padding(im, 4)
                if rgb:
                    batch_x.append(rgb_preprocessor(im))
                else:
                    batch_x.append(im)
                gt = manual_padding(gt, 4)
                batch_y.append(gt)
                n_samples += 1
                b += 1

        if not count_samples_mode:
            yield np.array(batch_x), np.array(batch_y)


# The version with the previous data augmentation strategy. The one used in the paper (without data augmentation)
def train_image_generator_legacy(paths, input_size, batch_size=1, count_samples_mode=False,
                                 rgb_preprocessor=None, data_augmentation=True):
    _, n_images = paths.shape
    rgb = True if rgb_preprocessor else False

    # All available transformations for data augmentation. 'None', 1.0 and 0 imply no change
    if data_augmentation:
        noises = [None, "gauss", "s&p"]  # s&p = salt and pepper
        alphas = [1.0, 0.8]  # Simple contrast control
        betas = [0, -50, 50]  # Simple brightness control
        rotations = [None, 90.0, 180.0, 270.0]  # Degrees
        flips = [None, "h", "v"]  # Horizontal, Vertical

    # This means no noise, no illumination adjustment, no rotation and no flip (i.e. only the original image is
    # provided)
    else:
        noises = [None]
        alphas = [1.0]
        betas = [0]
        rotations = [None]
        flips = [None]

    n_transformations = len(noises) * len(alphas) * len(betas) * len(rotations) * len(flips)

    i = -1
    j = n_transformations
    prev_im = False

    n_samples = 0

    while True:
        batch_x = []
        batch_y = []
        b = 0
        while b < batch_size:
            if j == n_transformations:
                j = 0
                i += 1

                if i == n_images:
                    if count_samples_mode:
                        yield n_samples
                    i = 0
                    n_samples = 0
                    np.random.shuffle(paths.transpose())

                if count_samples_mode:
                    print("\r%s/%s paths analyzed so far" % (str(i + 1).zfill(len(str(n_images))), n_images), end='')

                im_path = paths[0][i]
                gt_path = paths[1][i]

                or_im = get_image(im_path)
                or_gt = get_gt_image(gt_path)

                ims = np.zeros((n_transformations, or_im.shape[0], or_im.shape[1], or_im.shape[2]), dtype=or_im.dtype)
                gts = np.zeros((n_transformations, or_gt.shape[0], or_gt.shape[1], or_gt.shape[2]), dtype=or_gt.dtype)
                channel = 0

                for noise in noises:
                    noisy = noisy_version(or_im, noise)

                    for alpha in alphas:
                        for beta in betas:
                            adjusted = illumination_adjustment_version(noisy, alpha, beta)

                            for rotation in rotations:
                                rotated = rotated_version(adjusted, rotation)
                                rotated_gt = rotated_version(or_gt, rotation)

                                for flip in flips:
                                    flipped = flipped_version(rotated, flip)
                                    flipped_gt = flipped_version(rotated_gt, flip)
                                    if ims[channel, :, :, :].shape == flipped.shape:
                                        ims[channel, ...] = flipped
                                        gts[channel, ...] = flipped_gt
                                    else:
                                        flipped = cv2.resize(flipped, (or_im.shape[1], or_im.shape[0]))
                                        if len(flipped.shape) == 2:
                                            flipped = flipped[..., None]
                                        ims[channel, ...] = flipped
                                        flipped_gt = cv2.resize(flipped_gt, (or_gt.shape[1], or_gt.shape[0]))
                                        if len(flipped_gt.shape) == 2:
                                            flipped_gt = flipped_gt[..., None]
                                        gts[channel, ...] = flipped_gt
                                    channel += 1

            im = ims[j, ...]
            gt = gts[j, ...]

            if input_size:
                if not prev_im:
                    win_gen = crop_generator(im, gt, input_size)
                    prev_im = True
                try:
                    [im, gt] = next(win_gen)
                    im = manual_padding(im, 4)
                    gt = manual_padding(gt, 4)
                    if rgb:
                        batch_x.append(rgb_preprocessor(im))
                    else:
                        batch_x.append(im)
                    batch_y.append(gt)
                    n_samples += 1
                    b += 1
                except StopIteration:
                    prev_im = False
                    j += 1

            else:
                im = manual_padding(im, 4)
                if rgb:
                    batch_x.append(rgb_preprocessor(im))
                else:
                    batch_x.append(im)
                gt = manual_padding(gt, 4)
                batch_y.append(gt)
                n_samples += 1
                b += 1
                j += 1

        if not count_samples_mode:
            yield np.array(batch_x), np.array(batch_y)


# Test model on images
def get_preprocessor(model):
    """
    :param model: A Tensorflow model
    :return: A preprocessor corresponding to the model name
    Model name should match with the name of a model from
    https://www.tensorflow.org/api_docs/python/tf/keras/applications/
    This assumes you used a model with RGB inputs as the first part of your model,
    therefore your input data should be preprocessed with the corresponding
    'preprocess_input' function.
    If the model model is not part of the keras applications models, None is returned
    """
    try:
        m = importlib.import_module('tensorflow.keras.applications.%s' % model.name)
        return getattr(m, "preprocess_input")
    except ModuleNotFoundError:
        return None


def save_results_on_paths(model, paths, save_to="results", normalize_x=True, rgb_preprocessor=None):
    if not os.path.exists(save_to):
        os.makedirs(save_to)

    for path_index in range(paths.shape[-1]):
        im_name = os.path.split(paths[0, path_index])[-1]
        im_name, im_extension = os.path.splitext(im_name)
        im_name += ".png"
        compound_image = test_image_from_path(model, paths[0, path_index], paths[1, path_index], rgb_preprocessor)
        for im in range(len(compound_image)):
            if len(compound_image[im].shape) < 3:
                compound_image[im] = compound_image[im][..., None]
            if compound_image[im].shape[-1] == 1:
                compound_image[im] = np.concatenate([compound_image[im] for j in range(3)], axis=-1)
        cv2.imwrite(os.path.join(save_to, im_name),
                    255 * np.concatenate([compound_image[0], compound_image[1], compound_image[2]], axis=1))
        print("\r%s/%s paths analyzed so far" % (str(path_index + 1).zfill(len(str(paths.shape[-1]))), paths.shape[-1]),
              end='')


def test_image_from_path(model, input_path, gt_path, rgb_preprocessor=None, verbose=0):
    if rgb_preprocessor is None:
        rgb_preprocessor = get_preprocessor(model)
    rgb = True if rgb_preprocessor else False
    if rgb:
        prediction = model.predict(
            rgb_preprocessor(get_image(input_path))[None, ...], verbose=verbose)[0, ...]

    if gt_path:
        gt = get_gt_image(gt_path)[..., 0]
    input_image = cv2.cvtColor(get_image(input_path), cv2.COLOR_BGR2GRAY)[..., None] / 255.0
    if gt_path:
        return [input_image, gt, prediction]
    return [input_image, None, prediction]


# Compare GT and predictions from images obtained by save_results_on_paths()
def highlight_cracks(or_im, mask, bg_color, fade_intensity):
    highlight_mask = np.zeros(mask.shape, dtype=np.float)
    if bg_color == "black":
        highlight_mask[np.where(mask >= 128)] = 1.0
        highlight_mask[np.where(mask < 128)] = fade_intensity
    else:
        highlight_mask[np.where(mask >= 128)] = fade_intensity
        highlight_mask[np.where(mask < 128)] = 1.0
    return or_im * highlight_mask


def compare_masks(gt_mask, pred_mask, bg_color):
    if bg_color == "black":
        new_image = np.zeros(gt_mask.shape, dtype=np.float32)
        new_image[..., 2][np.where(pred_mask[..., 0] >= 128)] = 255
        new_image[..., 0][np.where(gt_mask[..., 0] >= 128)] = 255
        new_image[..., 1][np.where((new_image[..., 0] == 255) & (new_image[..., 2] == 255))] = 255
        new_image[..., 0][np.where((new_image[..., 0] == 255) & (new_image[..., 2] == 255))] = 0
        new_image[..., 2][
            np.where((new_image[..., 0] == 0) & (new_image[..., 1] == 255) & (new_image[..., 2] == 255))] = 0
    else:
        new_image = 255 * np.ones(gt_mask.shape, dtype=np.float32)
        new_image[..., 0][np.where(pred_mask[..., 0] < 128)] = 0
        new_image[..., 2][np.where(gt_mask[..., 0] < 128)] = 0
        new_image[..., 1][
            np.where((new_image[..., 0]) == 0 & (new_image[..., 1] == 255) & (new_image[..., 2] == 255))] = 0
        new_image[..., 1][
            np.where((new_image[..., 2]) == 0 & (new_image[..., 0] == 255) & (new_image[..., 1] == 255))] = 0
        new_image[..., 1][
            np.where((new_image[..., 0] == 0) & (new_image[..., 1] == 0) & (new_image[..., 2] == 0))] = 255

    return new_image


def analyze_gt_pred(im, gt, pred, bg_color, fade_intensity):
    if bg_color == "white":
        gt = 255 - gt
        pred = 255 - pred
    gt_highlight_cracks = highlight_cracks(im, gt, bg_color, fade_intensity)
    pred_highlight_cracks = highlight_cracks(im, pred, bg_color, fade_intensity)
    comparative_mask = compare_masks(gt, pred, bg_color)
    white_line_v = 255 * np.ones((comparative_mask.shape[0], 1, 3))
    first_row = np.concatenate(
        (im, white_line_v, gt_highlight_cracks, white_line_v, pred_highlight_cracks, white_line_v, comparative_mask),
        axis=1)
    white_line_h = 255 * np.ones((1, first_row.shape[1], 3))

    gt_highlight_cracks = highlight_cracks(255 - im, gt, bg_color, fade_intensity)
    pred_highlight_cracks = highlight_cracks(255 - im, pred, bg_color, fade_intensity)
    second_row = np.concatenate(
        (255 - im, white_line_v, gt_highlight_cracks, white_line_v, pred_highlight_cracks, white_line_v,
         comparative_mask), axis=1)
    return np.concatenate((first_row, white_line_h, second_row), axis=0)


def analyse_resulting_image(image_path, bg_color, fade_intensity):
    or_im = cv2.imread(image_path).astype(np.float)
    h, w, c = or_im.shape
    w = int(w / 3)
    im = or_im[:, :w, :]
    gt = or_im[:, w:2 * w, :]
    pred = or_im[:, 2 * w:, :]
    return analyze_gt_pred(im, gt, pred, bg_color, fade_intensity)


def analyse_resulting_image_folder(folder_path, bg_color="white", fade_intensity=0.1, new_folder=None):
    if not new_folder:
        new_folder = folder_path + "_mask_comparison"
    if not os.path.exists(new_folder):
        os.makedirs(new_folder)

    image_names = sorted([f for f in os.listdir(folder_path)
                          if not f.startswith(".") and (f.endswith(".png") or f.endswith(".jpg"))],
                         key=lambda f: f.lower())

    iteration = 0
    for name in image_names:
        iteration += 1
        print("\rImages processed: %s/%s" % (iteration, len(image_names)), end='')
        cv2.imwrite(os.path.join(new_folder, name),
                    analyse_resulting_image(os.path.join(folder_path, name), bg_color, fade_intensity))
    print("\rImages processed: %s/%s" % (iteration, len(image_names)))


def overlay_transform_resulting_image_folder(folder_path, new_folder=None):
    if not new_folder:
        new_folder = folder_path + "_highlighted segmentation"
    if not os.path.exists(new_folder):
        os.makedirs(new_folder)

    image_names = sorted([f for f in os.listdir(folder_path)
                          if not f.startswith(".") and (f.endswith(".png") or f.endswith(".jpg"))],
                         key=lambda f: f.lower())

    iteration = 0
    for name in image_names:
        or_im = cv2.imread(os.path.join(folder_path, name)).astype(np.float)
        h, w, c = or_im.shape
        w = int(w / 3)
        im = or_im[:, :w, :]
        pred = np.where(or_im[:, 2 * w:, 0]/255.0 >= 0.5, 255.0, 0.0)
        im[..., 2] = np.maximum(im[..., 2], pred)
        cv2.imwrite(os.path.join(new_folder, name), im)
        iteration += 1
        print("\rImages processed: %s/%s" % (iteration, len(image_names)), end='')
    print("\rImages processed: %s/%s" % (iteration, len(image_names)))


def join_overlay_folders(paths, new_folder="overlay_comparisons"):
    if not os.path.exists(new_folder):
        os.makedirs(new_folder)

    image_names = sorted([f for f in os.listdir(paths[0])
                          if not f.startswith(".") and (f.endswith(".png") or f.endswith(".jpg"))],
                         key=lambda f: f.lower())

    for name in image_names:
        comparison = np.concatenate([cv2.imread(os.path.join(folder_path, name)) for folder_path in paths], axis=1)
        cv2.imwrite(os.path.join(new_folder, name), comparison)

    with open(os.path.join(new_folder, "origin_folders.txt"), "w+") as f:
        f.write("\n".join(paths))


def calculate_thresholded_dsc_from_image_folder(folder_path):

    image_names = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path)
                          if not f.startswith(".") and (f.endswith(".png") or f.endswith(".jpg"))],
                         key=lambda f: f.lower())
    results_file = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path)
                          if not f.startswith(".") and f.endswith(".txt")],
                         key=lambda f: f.lower())[-1]

    scores = np.zeros((len(image_names)), dtype=np.float)
    for i, path in enumerate(image_names):
        print("\rImages processed: %s/%s" % (i, len(image_names)), end='')

        or_im = cv2.imread(path).astype(np.float)
        h, w, c = or_im.shape
        w = int(w / 3)
        gt = np.where(or_im[:, w:2 * w, 0]/255.0 >= 0.5, 1.0, 0.0)
        pred = np.where(or_im[:, 2 * w:, 0]/255.0 >= 0.5, 1.0, 0.0)
        intersection = pred * gt
        scores[i] = (2 * np.sum(intersection) + 1) / (np.sum(pred) + np.sum(gt) + 1)
    print("\rImages processed: %s/%s" % (i+1, len(image_names)))
    dsc = np.average(scores)

    with open(results_file, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if "dice" in line:
            elements = line.split(": ")
            elements[-1] = "{:.4f}\n".format(dsc)
            lines[i] = ": ".join(elements)
            break

    with open(results_file, "w") as f:
        f.write("".join(lines))


def calculate_scores_from_image_folder(folder_path):
    calculate_tolerant_scores_from_image_folder(folder_path, tolerance=0)


def calculate_tolerant_scores_from_image_folder(folder_path, tolerance=2):
    
    results_folder = "results_tolerant_%s_pixels" % tolerance
    folder_root = os.path.split(folder_path)[0]
    if not os.path.exists(os.path.join(folder_root, results_folder)):
        os.makedirs(os.path.join(folder_root, results_folder))
    image_names = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path)
                          if not f.startswith(".") and (f.endswith(".png") or f.endswith(".jpg"))],
                         key=lambda f: f.lower())
    
    n_images = len(image_names)
    score_names = ['precision', 'recall', 'f-score']
    scores = np.zeros((n_images, len(score_names)))
    string_list = [','.join(['image'] + score_names)]
    
    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*tolerance + 1, 2*tolerance + 1))
    for i, path in enumerate(image_names):
        print("\rImages processed: %s/%s" % (i, len(image_names)), end='')
        
        current_string_list = [folder_root] + ['' for n in score_names]
        score_dict = {}

        or_im = cv2.imread(path).astype(np.float)
        h, w, c = or_im.shape
        w = int(w / 4)

        gt = np.where(or_im[:, w:2 * w, 0] / 255.0 >= 0.5, 1.0, 0.0)
        if tolerance > 0:
            tolerant_gt = cv2.dilate(gt,se, borderType=cv2.BORDER_REFLECT_101)
        else:
            tolerant_gt = gt
        pred = np.where(or_im[:, 2 * w:3 * w, 0] / 255.0 >= 0.5, 1.0, 0.0)

        tp = pred * tolerant_gt
        fp = pred - tp
        fn = np.maximum(0, (1 - pred) - (1 - gt))

        confusion_matrix = np.zeros((2, 2))
        confusion_matrix[0, 0] = np.sum(tp)
        confusion_matrix[0, 1] = np.sum(fp)
        confusion_matrix[1, 0] = np.sum(fn)
        confusion_matrix[1, 1] = h * w - np.sum(tp) - np.sum(fp) - np.sum(fn)

        score_dict['precision'], score_dict['recall'], score_dict['f-score'] = calculate_PRF(confusion_matrix)
        
        for key in score_dict.keys():
            scores[i, score_names.index(key)] = score_dict[key]
            current_string_list[score_names.index(key) + 1] = "{:.4f}".format(score_dict[key])
        string_list.append(",".join(current_string_list))

        output_image = np.concatenate((fn[..., None], tp[..., None], fp[..., None]), axis=-1)  # In BGR format
        cv2.imwrite(os.path.join(folder_root, results_folder, os.path.split(path)[-1]), 255*output_image)

    print("\rImages processed: %s/%s" % (i + 1, len(image_names)))

    current_string_list = []
    summary_string_list = []
    average_scores = np.average(scores, axis=0)
    for i, score in enumerate(average_scores):
        current_string_list.append("{:.4f}".format(score))
        summary_string_list.append("{}: {:.4f}".format(score_names[i], score))
    current_string_list = ['average'] + current_string_list
    string_list.append(",".join(current_string_list))

    summary_string = "\n".join(summary_string_list)
    with open(os.path.join(folder_root, results_folder, "scores_summary.txt"), 'w+') as f:
        f.write(summary_string)

    results_string = "\n".join(string_list)
    with open(os.path.join(folder_root, results_folder, "scores.csv"), 'w+') as f:
        f.write(results_string)


def evaluate_model_on_paths(model, paths, output_folder, args):
    prediction_folder = os.path.join(output_folder, "predictions")
    if not os.path.exists(prediction_folder):
        os.makedirs(prediction_folder)

    evaluation_folder = os.path.join(output_folder, "evaluation")
    if not os.path.exists(evaluation_folder):
        os.makedirs(evaluation_folder)

    n_images = paths.shape[-1]
    input_images = ['' for i in range(n_images)]
    pred_images = ['' for i in range(n_images)]
    dir_names = []
    for path in paths.transpose():
        gt_path = path[1]
        dir_path, name = os.path.split(gt_path)
        dir_name = os.path.split(dir_path)[-1]
        if not (dir_name in dir_names):
            dir_names.append(dir_name)
    if len(dir_names) > 1:
        for dir_name in dir_names:
            if not os.path.exists(os.path.join(prediction_folder, dir_name)):
                os.makedirs(os.path.join(prediction_folder, dir_name))
            if not os.path.exists(os.path.join(evaluation_folder, dir_name)):
                os.makedirs(os.path.join(evaluation_folder, dir_name))
    print("Saving predictions...")
    bar_size = 10
    for i, path in enumerate(paths.transpose()):
        n_stars = round(bar_size * (i + 1) / n_images)
        print("\r[" + "*" * n_stars + " " * (bar_size - n_stars) + "]", end='')

        img_path = path[0]
        gt_path = path[1]
        input_images[i] = "%s;%s" % (img_path, gt_path)

        dir_path, name = os.path.split(gt_path)
        dir_name = os.path.split(dir_path)[-1]
        name, extension = os.path.splitext(name)
        # extension = ".png"

        [im, gt, pred] = test_image_from_path(model, img_path, gt_path, rgb_preprocessor=None)

        x_color = cv2.imread(img_path)
        or_shape = x_color.shape
        gt = gt[:or_shape[0], :or_shape[1]]
        pred = pred[:or_shape[0], :or_shape[1], 0]

        # x = cv2.cvtColor(x_color, cv2.COLOR_BGR2GRAY)
        y = gt
        y_pred = np.where(pred >= 0.5, 1.0, 0.0)

        if len(dir_names) > 1:
            pred_path = os.path.join(prediction_folder, dir_name, "%s%s" % (name, extension))
        else:
            pred_path = os.path.join(prediction_folder, "%s%s" % (name, extension))
        cv2.imwrite(pred_path, 255 * pred)
        pred_images[i] = "%s;%s" % (img_path, pred_path)

        y_color = 255 * np.concatenate([y[..., None] for c in range(3)], axis=-1).astype(np.uint8)
        y_pred_color = 255 * np.concatenate([y_pred[..., None] for c in range(3)], axis=-1).astype(np.uint8)
        pred_comparison = compare_masks(255 - y_color, 255 - y_pred_color, bg_color='white').astype(np.uint8)
        comparative_image = np.concatenate([x_color, y_color, y_pred_color, pred_comparison], axis=1)
        if len(dir_names) > 1:
            comparison_path = os.path.join(evaluation_folder, dir_name, "%s%s" % (name, extension))
        else:
            comparison_path = os.path.join(evaluation_folder, "%s%s" % (name, extension))
        cv2.imwrite(comparison_path, comparative_image)
    print("")

    input_text_dataset_path = "temp_input.txt"
    with open(input_text_dataset_path, 'w+') as f:
        f.write("\n".join(input_images))
    pred_text_dataset_path = "temp_output.txt"
    with open(pred_text_dataset_path, 'w+') as f:
        f.write("\n".join(pred_images))
    command = "python calculate_scores.py -d %s -p %s -pred %s --save_to %s" % \
              ("text", input_text_dataset_path, pred_text_dataset_path, evaluation_folder)
    print("Calculating and saving scores...")
    subprocess.run(command, shell=True)
    os.remove(input_text_dataset_path)
    os.remove(pred_text_dataset_path)

    parameters_string = "\n"
    for attribute in args.__dict__.keys():
        parameters_string += "\n--%s: %s" % (attribute, str(args.__getattribute__(attribute)))
    with open(os.path.join(evaluation_folder, "scores_summary.txt"), 'a') as f:
        f.write(parameters_string)

def corrected_crop_generator(im, gt, corrected_gt, input_size):
    corners = get_corners(im, input_size)
    for corner in corners:
        x = im[corner[0]:corner[0] + input_size[0], corner[1]:corner[1] + input_size[1], ...]
        y = gt[corner[0]:corner[0] + input_size[0], corner[1]:corner[1] + input_size[1], ...]
        corrected_y = corrected_gt[corner[0]:corner[0] + input_size[0], corner[1]:corner[1] + input_size[1], ...]
        yield [x, y, corrected_y]


# Apply a random transformation to an input pair
def corrected_random_transformation(im, gt, corrected_gt, **kwargs):
    noise = random.choice(kwargs["noises"])
    alpha = random.choice(kwargs["alphas"])
    beta = random.choice(kwargs["betas"])
    flip = random.choice(kwargs["flips"])
    zoom = random.choice(kwargs["zooms"])
    rot_ang = random.choice(kwargs["rot_angs"])
    shear_ang = random.choice(kwargs["shear_angs"])

    noisy = noisy_version(im, noise)
    adjusted = illumination_adjustment_version(noisy, alpha, beta)

    flipped = flipped_version(adjusted, flip)
    flipped_gt = flipped_version(gt, flip)
    corrected_flipped_gt = flipped_version(corrected_gt, flip)

    affine_transformed = image.apply_affine_transform(flipped, rot_ang, shear=shear_ang, zx=zoom, zy=zoom,
                                                      fill_mode="reflect")
    affine_transformed_gt = image.apply_affine_transform(flipped_gt, rot_ang, shear=shear_ang, zx=zoom, zy=zoom,
                                                         fill_mode="reflect")
    corrected_affine_transformed_gt = image.apply_affine_transform(corrected_flipped_gt, rot_ang, shear=shear_ang,
                                                                   zx=zoom, zy=zoom, fill_mode="reflect")

    return affine_transformed, np.where(affine_transformed_gt > 0.5, 1.0, 0.0), np.where(corrected_affine_transformed_gt > 0.5, 1.0, 0.0)


# This function allows to introduce a corrected version of the provided ground-truth, to create a weight mask for
# training
def corrected_validation_image_generator(paths, corrected_paths, batch_size=1, rgb_preprocessor=None):
    _, n_images = paths.shape
    rgb = True if rgb_preprocessor else False
    i = 0
    # remove_this_batch_number = 0
    while True:
        # remove_this_batch_number += 1
        batch_x = []
        batch_y = []
        b = 0
        while b < batch_size:
            if i == n_images:
                i = 0
            im_path = paths[0][i]
            gt_path = paths[1][i]
            corrected_gt_path = corrected_paths[1][i]

            im = get_image(im_path)
            gt = get_gt_image(gt_path)
            corrected_gt = get_gt_image(corrected_gt_path)
            if rgb:
                batch_x.append(rgb_preprocessor(im))
            else:
                batch_x.append(im)
            batch_y.append(np.concatenate([gt, (1 - cv2.bitwise_xor(gt, corrected_gt))[..., None]], axis=-1))
            b += 1
            i += 1

        # remove_this
        # if not os.path.exists("remove_this_2"):
        #     os.makedirs("remove_this_2")
        # for n_img, array in enumerate(batch_y):
        #     cv2.imwrite("remove_this_2/batch{:03d}_img{:02d}_gt.png".format(remove_this_batch_number, n_img),
        #                 255 * array[..., 0])
        #     cv2.imwrite("remove_this_2/batch{:03d}_img{:02d}_mask.png".format(remove_this_batch_number, n_img),
        #                 255 * array[..., 1])
        # # remove_this
        yield np.array(batch_x), np.array(batch_y)


# This function allows to introduce a corrected version of the provided ground-truth, to create a weight mask for
# training
def corrected_train_image_generator(paths, corrected_paths, input_size, batch_size=1, count_samples_mode=False,
                          rgb_preprocessor=None, data_augmentation=True):
    _, n_images = paths.shape
    all_paths = np.concatenate((paths, corrected_paths), axis=0)
    rgb = True if rgb_preprocessor else False

    # All available transformations for data augmentation
    if data_augmentation:
        augmentation_params = {
            "noises": [None, "gauss", "s&p"],
            "alphas": [1.0, 0.8],  # Simple contrast control
            "betas": [None, "bright", "dark"],  # Simple brightness control
            "flips": [None, "h", "v"],  # Horizontal, Vertical
            "zooms": [1.0, 2.0, 1.5],  # Zoom rate in both axis; >1.0 zooms out
            "rot_angs": [i * 5.0 for i in range(int(90.0 / 5.0 + 1))],  # Rotation angle in degrees
            "shear_angs": [i * 5.0 for i in range(int(45.0 / 5.0 + 1))]  # Shear angle in degrees
        }

    # This means no noise, no illumination adjustment, no rotation and no flip (i.e. only the original image is
    # provided)
    else:
        augmentation_params = {
            "noises": [None],  # s&p = salt and pepper
            "alphas": [1.0],  # Simple contrast control
            "betas": [None],  # Simple brightness control
            "flips": [None],  # Horizontal, Vertical
            "zooms": [1.0],  # Zoom rate in both axis; >1.0 zooms out
            "rot_angs": [0.0],  # Degrees
            "shear_angs": [0.0],  # Degrees
        }

    i = -1
    prev_im = False
    n_samples = 0
    # remove_this_batch_number = 0
    while True:
        # remove_this_batch_number += 1
        batch_x = []
        batch_y = []
        b = 0
        while b < batch_size:

            if not prev_im:
                i += 1

                if i == n_images:
                    if count_samples_mode:
                        yield n_samples
                    i = 0
                    # np.random.shuffle(paths.transpose())
                    np.random.shuffle(all_paths.transpose())

                if count_samples_mode:
                    print("\r%s/%s paths analyzed so far" % (str(i + 1).zfill(len(str(n_images))), n_images), end='')

                im_path = all_paths[0][i]
                gt_path = all_paths[1][i]
                corrected_gt_path = all_paths[3][i]

                or_im = get_image(im_path)
                or_gt = get_gt_image(gt_path)
                corrected_or_gt = get_gt_image(corrected_gt_path)

            if input_size:
                if not prev_im:
                    win_gen = corrected_crop_generator(or_im, or_gt, corrected_or_gt, input_size)
                    prev_im = True
                try:
                    [im, gt, corrected_gt] = next(win_gen)
                except StopIteration:
                    prev_im = False
                    continue

                x, y, corrected_y = corrected_random_transformation(im, gt, corrected_gt, **augmentation_params)

                x = manual_padding(x, 4)
                y = manual_padding(y, 4)
                corrected_y = manual_padding(corrected_y, 4)
                if rgb:
                    batch_x.append(rgb_preprocessor(x))
                else:
                    batch_x.append(x)
                batch_y.append(np.concatenate([y, (1 - cv2.bitwise_xor(y, corrected_y))[..., None]], axis=-1))
                n_samples += 1
                b += 1

            else:
                im, gt, corrected_gt = corrected_random_transformation(or_im, or_gt, corrected_or_gt, **augmentation_params)
                im = manual_padding(im, 4)
                if rgb:
                    batch_x.append(rgb_preprocessor(im))
                else:
                    batch_x.append(im)
                gt = manual_padding(gt, 4)
                corrected_gt = manual_padding(corrected_gt, 4)
                batch_y.append(np.concatenate([gt, (1 - cv2.bitwise_xor(gt, corrected_gt))[..., None]], axis=-1))
                n_samples += 1
                b += 1

        if not count_samples_mode:
            #remove_this
            # if not os.path.exists("remove_this"):
            #     os.makedirs("remove_this")
            # for n_img, array in enumerate(batch_y):
            #     cv2.imwrite("remove_this/batch{:03d}_img{:02d}_gt.png".format(remove_this_batch_number, n_img), 255*array[..., 0])
            #     cv2.imwrite("remove_this/batch{:03d}_img{:02d}_mask.png".format(remove_this_batch_number, n_img), 255*array[..., 1])
            #remove_this

            yield np.array(batch_x), np.array(batch_y)
