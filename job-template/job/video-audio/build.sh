#!/bin/bash

set -ex

docker build --network=host -t ccr.ccs.tencentyun.com/cube-studio/video-audio:20250301 -f job/video-audio/Dockerfile .
docker push ccr.ccs.tencentyun.com/cube-studio/video-audio:20250301





