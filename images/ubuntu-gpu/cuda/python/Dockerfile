ARG FROM_IMAGES
FROM ${FROM_IMAGES}

ARG PYTHON_VERSION

# 安装python
RUN add-apt-repository -y ppa:deadsnakes/ppa && apt update && apt install -y  libsasl2-dev libpq-dev python3-pip $PYTHON_VERSION-distutils
RUN set -x; rm -rf /usr/bin/python /usr/bin/python3; apt install -y --fix-missing ${PYTHON_VERSION} && ln -s /usr/bin/${PYTHON_VERSION} /usr/bin/python && ln -s /usr/bin/${PYTHON_VERSION} /usr/bin/python3

RUN bash -c "wget https://bootstrap.pypa.io/get-pip.py && python get-pip.py --ignore-installed" \
    && rm -rf /usr/bin/pip && ln -s /usr/bin/pip3 /usr/bin/pip

RUN pip install -U pip && pip install flask==3.1.0 requests==2.22.0 kubernetes==31.0.0 numpy==2.0.2 pandas==2.2.3 tornado==6.4.1 pysnooper==1.2.1 redis==5.2.0


