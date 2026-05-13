# docker build --network=host -t ccr.ccs.tencentyun.com/cube-studio/wait-pod:v1 .
# docker buildx build --platform linux/amd64,linux/arm64 -t ccr.ccs.tencentyun.com/cube-studio/wait-pod:v1 . --push
FROM python:3.9

ENV TZ=Asia/Shanghai
ENV DEBIAN_FRONTEND=noninteractive

RUN pip install pysnooper==1.2.1 psutil==6.1.0 requests==2.32.3 numpy==2.0.2 scikit-learn==1.5.2 kubernetes==28.1.0
COPY . /app/

WORKDIR /app
ENV PYTHONPATH=/app:${PYTHONPATH:-}

ENTRYPOINT ["python3", "launcher.py"]


