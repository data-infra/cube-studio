#!/bin/bash

docker build --network=host -t ccr.ccs.tencentyun.com/cube-studio/ray:gpu-20250301 -f job/ray/Dockerfile .
docker push ccr.ccs.tencentyun.com/cube-studio/ray:gpu-20250301



