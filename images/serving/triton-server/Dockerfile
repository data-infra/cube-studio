
ARG FROM_IMAGES
FROM $FROM_IMAGES

## 切换内部源
RUN apt update && apt-get install -y wget

ENV TZ Asia/Shanghai

# 安装运维工具
RUN apt update -y && apt install -y --no-install-recommends vim apt-transport-https gnupg2 ca-certificates-java rsync jq  wget git dnsutils iputils-ping net-tools curl zip

## 安装中文
#RUN apt install -y --no-install-recommends locales ttf-wqy-microhei ttf-wqy-zenhei xfonts-wqy && locale-gen zh_CN && locale-gen zh_CN.utf8
#ENV LANG zh_CN.UTF-8
#ENV LC_ALL zh_CN.UTF-8
#ENV LANGUAGE zh_CN.UTF-8

# 便捷操作
RUN echo "alias ll='ls -alF'" >> ~/.bashrc && \
    echo "alias la='ls -A'" >> ~/.bashrc && \
    echo "alias vi='vim'" >> ~/.bashrc

