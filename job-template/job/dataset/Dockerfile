FROM python:3.9

ENV TZ=Asia/Shanghai
ENV DEBIAN_FRONTEND=noninteractive
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple && \
    pip install pysnooper psutil requests huggingface_hub==0.29.1 hf_transfer==0.1.9 modelscope==1.23.2
COPY job/dataset/ /app/

WORKDIR /app
ENV PYTHONPATH=/app:${PYTHONPATH:-}

ENTRYPOINT ["python3", "launcher.py"]


