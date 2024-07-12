
# ubuntu 安装containerd

##  卸载旧版本containerd
```bash
sudo apt-get remove docker docker-engine docker.io containerd runc
sudo rm -rf /var/lib/docker
sudo rm -rf /var/lib/containerd
```

## 安装containerd

```bash
# 安装containerd
sudo apt-get update
sudo apt-get install -y containerd.io

# 查看版本
apt-cache madison containerd

# sudo apt-get install containerd=<VERSION>

# 查看运行状态
systemctl enable containerd
systemctl status containerd
```

# 配置containerd

```bash
vi /etc/containerd/config.toml

添加如下配置

    [plugins."io.containerd.grpc.v1.cri".registry]
      [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
        [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
          # 添加下面这一行
          endpoint = ["https://hub.uuuadc.top", "https://docker.anyhub.us.kg", "https://dockerhub.jobcher.com", "https://dockerhub.icu", "https://docker.ckyl.me", "https://docker.awsl9527.cn"]
          
systemctl restart containerd
```



