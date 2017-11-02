import keras
from keras.datasets import cifar10
from sklearn.cluster import KMeans
from PIL import Image
import numpy as np
import os
import argparse
import utils
import pickle
import models
import shutil

curdir = os.path.dirname(os.path.abspath(__file__))
parser = argparse.ArgumentParser()
parser.add_argument('zgenerater_weights')
parser.add_argument('--use_centroids', type=bool, default=False)
parser.add_arugment('--imgs_per_centroid', type=int, default=50)
parser.add_argument('--result_root', default=os.path.join(curdir, 'result'))
parser.add_argument('--pred_batch_size', type=int, default=100)

def main(args):

    # ===============================
    # Instantiate zgenerater(encoder)
    # ===============================
    zgenerater = models.create_zgenerater()
    zgenerater.load_weights(args.zgenerater_weights)

    # ===============================
    # Prepare dataset
    # ===============================
    # make input datasets
    (_, _), (x_test, y_test) = cifar10.load_data()
    x_test = x_test.astype(np.float32)
    x_test = utils.preprocess_input(x_test)

    # convert all images into encoded vector points
    print("converting all images into latent z variables..")
    input_data = zgenerater.predict(
        x_test,
        batch_size=args.pred_batch_size,
        verbose=0)
    input_data = input_data.reshape(len(x_test), input_data.shape[-1])

    # ===============================
    # k-means clustering
    # ===============================
    classes = [
        'airplane',
        'automobile',
        'bird',
        'cat',
        'deer',
        'dog',
        'frog',
        'horse',
        'ship',
        'truck',
    ]
    num_classes = len(classes)

    # compute centroids
    if args.use_centroids:
        centroids = []
        for i in range(len(classes)):
            ind = (y_test == i)
            sample = (x_test[ind])[:args.imgs_per_centroid]
            out = zgenerater.predict_on_batch(sample)
            out = out.reshape(len(sample), out.shape[-1])
            centroid = np.mean(out, axis=0)
            centroids.append(centroid)
        centroids = np.array(centroids)
        print(centroids.shape)

    # clustering
    print("clustering has started...")
    kmeans = KMeans(n_clusters=num_classes)
    kmeans.fit(x)

    # ===============================
    # Save results
    # ===============================
    if os.path.exists(args.result_root) == False:
        os.makedirs(args.result_root)

    # save k-means result as pickle file
    with open(os.path.join(args.result_root, 'kmeans.pkl'), 'wb') as fp:
        pickle.dump(kmeans, fp)

    # classify images
    for i in range(num_classes):
        dirname = os.path.join(args.result_root, 'class_%d' % i)
        if os.path.exists(dirname) == False:
            os.mkdir(dirname)
        ind = (kmeans.labels_ == i)
        imgs = x_test[ind]
        labels = y_test[ind]
        for j in range(len(imgs)):
            img = utils.decode_output(imgs[j])
            img = img.astype(np.uint8)
            img = Image.fromarray(img)
            label = classes[int(labels[j])]
            dst = os.path.join(dirname, '%s_%d.png' % (label, j))
            img.save(dst)


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
