# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import time
import argparse
import logging
import gzip
import struct
import numpy as np

from common import find_mxnet, fit
from common.util import download_file

if hasattr(find_mxnet, "add_mxnet_path"):
    find_mxnet.add_mxnet_path()

import mxnet as mx  # noqa: E402

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)

def read_data(label_fname, image_fname, data_dir):
    """
    下载并读取数据到numpy数组
    """
    # 原始url（保留）
    # base_url = 'http://yann.lecun.com/exdb/mnist/'
    base_url = 'http://docker-76009.sz.gfp.tencent-cloud.com/kubeflow/pytorch/example/data/'

    os.makedirs(data_dir, exist_ok=True)

    label_path = os.path.join(data_dir, label_fname)
    image_path = os.path.join(data_dir, image_fname)

    with gzip.open(download_file(base_url + label_fname, label_path), "rb") as flbl:
        _magic, _num = struct.unpack(">II", flbl.read(8))
        label = np.frombuffer(flbl.read(), dtype=np.int8)

    with gzip.open(download_file(base_url + image_fname, image_path), "rb") as fimg:
        _magic, _num, rows, cols = struct.unpack(">IIII", fimg.read(16))
        image = np.frombuffer(fimg.read(), dtype=np.uint8).reshape(len(label), rows, cols)

    return (label, image)


def to4d(img):
    """
    将图像数据转换为4D数组
    """
    return img.reshape(img.shape[0], 1, 28, 28).astype(np.float32) / 255.0


def shard_by_worker(lbl, img, kv):
    """
    按worker rank进行数据切分，避免每个worker都训练全量60k数据
    """
    if kv is None:
        return lbl, img

    try:
        num_workers = int(getattr(kv, "num_workers", 1))
        rank = int(getattr(kv, "rank", 0))
    except Exception:
        return lbl, img

    if num_workers <= 1:
        return lbl, img

    idx = np.arange(len(lbl))
    idx = idx[idx % num_workers == rank]
    return lbl[idx], img[idx]


def get_mnist_iter(args, kv):
    """
    使用NDArrayIter创建数据迭代器
    """
    (train_lbl, train_img) = read_data(
        'train-labels-idx1-ubyte.gz', 'train-images-idx3-ubyte.gz', args.data_dir
    )
    (val_lbl, val_img) = read_data(
        't10k-labels-idx1-ubyte.gz', 't10k-images-idx3-ubyte.gz', args.data_dir
    )

    # 分布式：切分训练数据（val默认不切，保证评估一致；如需也可切）
    train_lbl, train_img = shard_by_worker(train_lbl, train_img, kv)

    # 覆盖num_examples，确保每个worker的epoch steps正确
    args.num_examples = int(train_lbl.shape[0])

    train = mx.io.NDArrayIter(
        to4d(train_img), train_lbl, args.batch_size, shuffle=True, last_batch_handle="discard"
    )
    val = mx.io.NDArrayIter(
        to4d(val_img), val_lbl, args.batch_size, shuffle=False, last_batch_handle="pad"
    )
    return (train, val)


if __name__ == '__main__':
    env = os.environ
    role = env.get("DMLC_ROLE", "")

    logging.info("DMLC_ROLE=%s", role)
    logging.info("DMLC_PS_ROOT_URI=%s", env.get("DMLC_PS_ROOT_URI", ""))
    logging.info("DMLC_PS_ROOT_PORT=%s", env.get("DMLC_PS_ROOT_PORT", ""))
    logging.info("DMLC_NUM_SERVER=%s", env.get("DMLC_NUM_SERVER", ""))
    logging.info("DMLC_NUM_WORKER=%s", env.get("DMLC_NUM_WORKER", ""))

    # 解析参数
    parser = argparse.ArgumentParser(
        description="训练mnist数据集",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--num-classes', type=int, default=10, help='分类数量')
    parser.add_argument('--num-examples', type=int, default=60000, help='训练样本数量')
    parser.add_argument('--add_stn', action="store_true", default=False,
                        help='添加空间变换网络层（仅lenet）')
    parser.add_argument('--data-dir', type=str, default=os.environ.get("DATA_DIR", "/tmp/mnist-data"),
                        help='mnist数据文件下载/存储路径')

    fit.add_fit_args(parser)
    parser.set_defaults(
        # 网络
        network='mlp',
        # 训练
        gpus=None,
        batch_size=64,
        disp_batches=10,
        num_epochs=20,
        lr=.05,
        lr_step_epochs='10',
        # 分布式默认不强行覆盖，交给启动命令的--kv-store
    )
    args = parser.parse_args()

    logging.info("Args: %s", vars(args))

    # 加载网络
    from importlib import import_module
    net = import_module('symbols.' + args.network)
    sym = net.get_symbol(**vars(args))

    t0 = time.time()
    fit.fit(args, sym, get_mnist_iter)
    logging.info("训练完成. 耗时=%.2fs", time.time() - t0)
