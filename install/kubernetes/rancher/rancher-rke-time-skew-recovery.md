# Rancher RKE 集群时间回拨恢复

## 现象

服务器重启后，`docker ps` 控制面容器显示 `Up Less than a second`，大量 Pod 异常，kube-apiserver 报 `service account token is not valid yet`。

## 原因

双系统（Windows + Linux）或 BIOS 用本地时间存 RTC，Linux 默认按 UTC 读取，导致开机时系统时间多 8 小时。Docker/K8s 在错误时间下启动，NTP 修正后 token 变成"未来签发"，apiserver 拒绝认证。

## 根治：防止再次发生

```bash
# 告诉 Linux 硬件时钟存的是本地时间，只需执行一次
sudo timedatectl set-local-rtc 1
```

## 恢复步骤

```bash
# 1. 用 RKE kubeconfig 查看集群状态
sudo kubectl --kubeconfig /etc/kubernetes/ssl/kubecfg-kube-node.yaml get node -o wide
sudo kubectl --kubeconfig /etc/kubernetes/ssl/kubecfg-kube-node.yaml get pod -A

# 2. 备份 k8s 容器列表
sudo docker ps -a --format "{{.ID}} {{.Names}} {{.Status}}" |
  awk '$2 ~ /^k8s_/ {print}' |
  sudo tee /tmp/k8s-containers-before-cleanup.txt

# 3. 停 kubelet → 清理 k8s_ 容器 → 启 kubelet
sudo docker stop kubelet
sudo docker ps -a --format "{{.ID}} {{.Names}}" |
  awk '$2 ~ /^k8s_/ {print $1}' |
  xargs -r sudo docker rm -f
sudo docker start kubelet

# 4. 等待 Pod 重建
sleep 60
sudo kubectl --kubeconfig /etc/kubernetes/ssl/kubecfg-kube-node.yaml get pod -A

# 5. 修正控制面容器的时间显示（可选，仅解决 docker ps 显示问题）
sudo docker restart etcd && sleep 8
sudo docker restart kube-apiserver && sleep 8
sudo docker restart kube-controller-manager kube-scheduler kube-proxy

# 6. 验证
sudo kubectl --kubeconfig /etc/kubernetes/ssl/kubecfg-kube-node.yaml get pod -A |
  awk 'NR==1 || ($4 != "Running" && $4 != "Completed") {print}'
sudo docker ps --format "{{.Names}} {{.Status}}" |
  egrep "^(etcd|kube-apiserver|kubelet|kube-proxy|kube-scheduler|kube-controller-manager|myrancher) "
```

## 注意

- 只删 `k8s_` 开头的 Pod 容器，不要 `docker rm -f $(docker ps -aq)`，会误删控制面容器
- 不会删除 etcd 数据、Docker volume、PVC、镜像，MySQL/PostgreSQL/MinIO 等数据不受影响
- 宿主机直接 `kubectl` 报 `localhost:8080 refused` 是因为没加 `--kubeconfig`，不代表集群挂了
