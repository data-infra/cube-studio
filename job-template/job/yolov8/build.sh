#!/bin/bash

set -ex

docker build --network=host -t ccr.ccs.tencentyun.com/cube-studio/yolov8:20250901 -f Dockerfile  .
docker push ccr.ccs.tencentyun.com/cube-studio/yolov8:20250901




#docker manifest rm ccr.ccs.tencentyun.com/cube-studio/yolov8:20250901
#docker manifest create ccr.ccs.tencentyun.com/cube-studio/yolov8:20250901 ccr.ccs.tencentyun.com/cube-studio/yolov8:20250901-amd64 ccr.ccs.tencentyun.com/cube-studio/yolov8:20250918-npu
#docker manifest push ccr.ccs.tencentyun.com/cube-studio/yolov8:20250901

