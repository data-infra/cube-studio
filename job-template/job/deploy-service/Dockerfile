
FROM python:3.9

ENV TZ=Asia/Shanghai
ENV DEBIAN_FRONTEND=noninteractive

RUN pip install kubernetes==28.1.0 pysnooper==1.2.1 psutil==6.1.0
COPY job/deploy-service/ /app/

WORKDIR /app
ENV PYTHONPATH=/app:${PYTHONPATH:-}

ENTRYPOINT ["python3", "launcher.py"]


