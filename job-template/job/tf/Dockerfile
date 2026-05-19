FROM python:3.9

ENV TZ=Asia/Shanghai
ENV DEBIAN_FRONTEND=noninteractive

ARG TARGETARCH

RUN wget https://github.com/stern/stern/releases/download/v1.33.1/stern_1.33.1_linux_${TARGETARCH}.tar.gz && tar -zxvf stern_1.33.1_linux_${TARGETARCH}.tar.gz && rm stern_1.33.1_linux_${TARGETARCH}.tar.gz && chmod +x stern &&  mv stern /usr/bin/stern

RUN /usr/local/bin/python -m pip install --upgrade pip && \
    pip install kubernetes==28.1.0 pysnooper==1.2.0 psutil==5.9.6 requests==2.31.0 numpy==1.26.2 pyinstaller==6.2.0 argparse==1.4.0
COPY job/tf/ /app/
COPY job/pkgs /app/job/pkgs
WORKDIR /app
ENV PYTHONPATH=/app:${PYTHONPATH:-}

ENTRYPOINT ["python3", "launcher.py"]

