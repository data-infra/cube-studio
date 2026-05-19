#!/bin/bash

set -ex

docker build --network=host -t ccr.ccs.tencentyun.com/cube-studio/video-audio:20260301 -f job/video-audio/Dockerfile .
docker push ccr.ccs.tencentyun.com/cube-studio/video-audio:20260301

# docker buildx build --platform linux/amd64,linux/arm64 -t ccr.ccs.tencentyun.com/cube-studio/video-audio:20260301 -f job/video-audio/Dockerfile . --push


