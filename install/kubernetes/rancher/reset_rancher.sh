#!/usr/bin/env bash 
# 先mv原有数据
mv /data/k8s /data/k8s1
# 删除rancher的基础容器
docker rm -f myrancher etcd service-sidekick kube-apiserver kube-controller-manager kube-scheduler kubelet kube-proxy share-mnt rke-worker-port-listener rke-cp-port-listener rke-etcd-port-listener
# 删除所有k8s的容器
docker stop $(sudo docker ps -a -q --filter "name=k8s_")
docker rm $(sudo docker ps -a -q --filter "name=k8s_")
# 删除所有未被使用的卷
docker volume prune
docker network prune

# 卸载所有挂载
for mount in $(mount | grep tmpfs | grep '/var/lib/kubelet' | awk '{ print $3 }') /var/lib/kubelet /var/lib/rancher; do umount $mount; done
for m in $(sudo tac /proc/mounts | sudo awk '{print $2}'|sudo grep /var/lib/kubelet);do
 sudo umount $m||true
done
for m in $(sudo tac /proc/mounts | sudo awk '{print $2}'|sudo grep /var/lib/rancher);do
 sudo umount $m||true
done

# 重置iptable
sudo iptables-save | grep -v -E '(KUBE-|cali|flannel)' | sudo iptables-restore

sudo rm -rf /var/lib/rancher/
sudo rm -rf /run/kubernetes/

sudo rm -rf /etc/ceph \
       /etc/cni \
       /etc/kubernetes \
       /opt/cni \
       /opt/rke \
       /run/secrets/kubernetes.io \
       /run/calico \
       /run/flannel \
       /var/lib/calico \
       /var/lib/etcd \
       /var/lib/cni \
       /var/lib/rancher/rke/log \
       /var/log/containers \
       /var/log/pods \
       /var/run/calico \
       /var/etcd


# sudo rm -rf /var/lib/kubelet/

sudo systemctl restart containerd
sudo systemctl restart docker

mv /data/k8s1 /data/k8s