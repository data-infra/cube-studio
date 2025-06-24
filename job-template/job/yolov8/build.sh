#!/bin/bash

set -ex

docker build --network=host -t ccr.ccs.tencentyun.com/cube-studio/yolov8:2025.06 -f Dockerfile  .
docker push ccr.ccs.tencentyun.com/cube-studio/yolov8:2025.06
