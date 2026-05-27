#!/bin/bash

set -ex

docker build --network=host -t ccr.ccs.tencentyun.com/cube-studio/deploy-service:20240601 -f job/deploy-service/Dockerfile .
docker push ccr.ccs.tencentyun.com/cube-studio/deploy-service:20240601



