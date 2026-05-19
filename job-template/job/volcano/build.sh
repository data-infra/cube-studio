#!/bin/bash

set -ex

docker build --network=host -t ccr.ccs.tencentyun.com/cube-studio/volcano:20250801 -f job/volcano/Dockerfile .
docker push ccr.ccs.tencentyun.com/cube-studio/volcano:20250801

# docker buildx build --platform linux/amd64,linux/arm64 -t ccr.ccs.tencentyun.com/cube-studio/volcano:20250801 -f job/volcano/Dockerfile . --push



