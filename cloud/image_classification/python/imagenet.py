"""
implementation of imagenet dataset
"""

# pylint: disable=unused-argument,missing-docstring

import logging
import os
import re
import time

import numpy as np
from PIL import Image

import dataset

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("imagenet")

_IMAGE_SIZE = [224, 224, 3]
_PREPROCESSED = "preprocessed"


class Imagenet(dataset.Dataset):

    def __init__(self, data_path, image_list, use_cache=0, image_format="NHWC", pre_process=None, count=None):
        super(Imagenet, self).__init__()
        self.image_list = []
        self.label_list = []
        self.count = count
        self.use_cache = use_cache
        self.cache_dir = os.path.join(data_path, _PREPROCESSED, image_format)
        self.data_path = data_path
        self.pre_process = pre_process
        self.need_transpose = True if image_format == "NCHW" else False
        not_found = 0
        if image_list is None:
            image_list = os.path.join(data_path, "val_map.txt")

        os.makedirs(self.cache_dir, exist_ok=True)

        start = time.time()
        with open(image_list, 'r') as f:
            for s in f:
                image_name, label = re.split(r"\s+", s.strip())
                src = os.path.join(data_path, image_name)
                dst = os.path.join(self.cache_dir, os.path.basename(image_name))
                if not os.path.exists(src):
                    # if the image does not exists ignore it
                    not_found += 1
                    continue
                if not os.path.exists(dst):
                    # cache a preprocessed version of the image
                    with Image.open(src) as img_org:
                        img = self.pre_process(img_org, need_transpose=self.need_transpose, dims=_IMAGE_SIZE)
                        with open(dst, "wb") as f:
                            img.tofile(f)

                if self.use_cache:
                    # if we use cache, preload the image
                    with open(dst, "rb") as f:
                        img = f.read()
                        img = np.frombuffer(img, dtype=np.float32)
                        img = img.reshape(_IMAGE_SIZE)
                        if self.need_transpose:
                            img = img.reshape(_IMAGE_SIZE[2], _IMAGE_SIZE[0], _IMAGE_SIZE[1])
                        else:
                            img = img.reshape(_IMAGE_SIZE)
                        self.image_list.append(img)
                else:
                    # else use the image path and load at inference time
                    self.image_list.append(dst)

                self.label_list.append(int(label))

                # limit the dataset if requested
                if self.count and len(self.image_list) > self.count:
                    break

        time_taken = time.time() - start
        if not self.image_list:
            log.error("no images in image list found")
            raise ValueError("no images in image list found")
        if not_found > 0:
            log.info("reduced image list, %d images not found", not_found)

        log.info("loaded {} images, cache={}, took={:.1f}sec".format(
            len(self.image_list), use_cache, time_taken))

        self.label_list = np.array(self.label_list)
        if use_cache:
            self.image_list = np.array(self.image_list)

    def get_item(self, nr):
        if self.use_cache:
            img = self.image_list[nr]
        else:
            with open(self.image_list[nr], "rb") as f:
                img = f.read()
                img = np.frombuffer(img, dtype=np.float32)
                if self.need_transpose:
                    img = img.reshape(_IMAGE_SIZE[2], _IMAGE_SIZE[0], _IMAGE_SIZE[1])
                else:
                    img = img.reshape(_IMAGE_SIZE)
        return img, self.label_list[nr]
