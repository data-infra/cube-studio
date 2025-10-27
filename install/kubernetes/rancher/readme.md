# 1. 机器初始化

参考install/rancher/install_docker.md部署docker

clone项目，git clone --depth=1 https://github.com/data-infra/cube-studio.git

centos中如果没有git，可以先yum install git安装git

## 1.1 git clone遇到问题“GnuTLS recv error (-110): The TLS connection was non-properly terminated.”

解决方案为依次执行以下命令：
apt-get install gnutls-bin
git config --global http.sslVerify false
git config --global http.postBuffer 1048576000

再执行git clone即可，如果还是不行，直接git clone --depth=1 https://githubfast.com/data-infra/cube-studio.git，通过国内代理拉取。

# 2. 建设前准备

1、自建docker镜像仓库或者直接使用云厂商免费镜像仓库。 如果内网无法连接到互联网的话，则可以使用Harbor自建一个内网仓库，并将私有仓库添加到docker的insecure-registries配置中。

2、如果内网是无法连接外网的，需要我们在机器上提前拉好镜像。 修改install/kubernetes/rancher/all_image.py中内网仓库地址，运行导出推送和拉取脚本。联网机器上运行 pull_rancher_images.sh将镜像推送到内网仓库 或 rancher_image_save.sh将镜像压缩成文件再导入到内网机器。 不能联网机器上运行，每台机器运行 pull_rancher_harbor.sh 从内网仓库中拉取镜像 或 rancher_image_load.sh 从压缩文件中导入镜像 。


# 3. centos8/centos8 stream/OpenCloudOS Server 8/Redhat 9 系统初始化

```bash
#修改/etc/firewalld/firewalld.conf
#FirewallBackend=nftables
#FirewallBackend=iptables

yum install -y yum-utils device-mapper-persistent-data lvm2
yum install -y iptables container-selinux iptables-services
# 加载内核模块
(
cat << EOF

systemctl stop firewalld
systemctl disable firewalld
systemctl stop iptables
systemctl disable iptables
systemctl stop ip6tables
systemctl disable ip6tables
systemctl stop nftables
systemctl disable nftables

modprobe br_netfilter 
modprobe ip_tables 
modprobe iptable_nat 
modprobe iptable_filter 
modprobe iptable_mangle 
modprobe iptable_mangle
modprobe ip6_tables 
modprobe ip6table_nat 
modprobe ip6table_filter 
modprobe ip6table_mangle 
modprobe ip6table_mangle

EOF
)>>  /etc/rc.d/rc.local
chmod +x /etc/rc.d/rc.local
sh /etc/rc.d/rc.local
# 查看加载的内核模块
lsmod
sudo echo 'ip_tables' >> /etc/modules


systemctl status iptables
systemctl status ip6tables
systemctl status nftables
systemctl status firewalld

modinfo iptable_nat
modinfo ip6table_nat

echo "net.bridge.bridge-nf-call-ip6tables = 1" >> /etc/sysctl.conf
echo "net.bridge.bridge-nf-call-iptables=1" >> /etc/sysctl.conf
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
echo "1" >/proc/sys/net/bridge/bridge-nf-call-iptables
sysctl -p

systemctl restart docker

reboot

# ipv6相关错误可以忽略
# 查看模块
# ls /lib/modules/`uname -r`/kernel/net/ipv6/netfilter/
```

# 4. 部署rancher server

单节点部署rancher server  

```bash
# 清理历史部署痕迹
cd cube-studio/install/kubernetes/rancher/
sh reset_docker.sh
进程关闭会有时延。
执行后
docker ps -a   查看是否还有剩余没清理干净的，如果有，重启机器，重新 sh reset_docker.sh

# 提前拉取需要的镜像
sh pull_rancher_images.sh 

如果拉取中碰到拉取失败的问题，配置好docker加速器后尝试通过“systemctl restart docker”重启docker，再次执行拉取脚本就可以了。

echo "127.0.0.1 localhost" >> /etc/hosts

# 部署rancher server
export RANCHER_CONTAINER_TAG=v2.8.5
export PASSWORD=cube-studio
sudo docker run -d --privileged --restart=unless-stopped -p 443:443 --name=myrancher -e AUDIT_LEVEL=3 -e CATTLE_BOOTSTRAP_PASSWORD=$PASSWORD rancher/rancher:$RANCHER_CONTAINER_TAG
# 打开 https://xx.xx.xx.xx:443/ 等待web界面可以打开。预计要1~10分钟
# 用户名admin，输入密码cube-studio
```

## 4.1 rancher server 启动可能问题

- 2 如果是centos 8的配置，按照文章上面的方法修改配置

- 3 机器docker 存储目录要>100G，内存>8G

- 4 要提前拉取镜像sh pull_rancher_images.sh  不然会因为拉取时间过长造成失败。如果拉取不了，可配置docker加速器，参考install/kubernetes/rancher/install_docker.md,

- 5、permission denied类型的报错，mount 查看所属盘是否有noexec 限制

- 6 查看rancher server的报错，`docker logs -f myrancher` 查看报错原因，忽略其中同步数据的错误。
 
  - 7 查看k3s的日志报错，在容器刚重启后，执行 `docker exec -it myrancher cat k3s.log > k3s.log` 将报错日志保存到本地，在日志中搜索error相关内容。

      7.1 如果k3s日志报错 iptable的问题，那就按照上面的centos8配置iptable，  

      7.2 如果k3s日志报错 containerd的问题，那就 `docker exec -it myrancher mv /var/lib/rancher/k3s/agent/containerd /varllib/rancher/k3slagent/_containerd`
    
      7.3 如果k3s日志报错系统内容中没有xx模块，那就降低linux系统版本
    
      7.4 如果k3s日志报错`Failed to set sysctl: open /proc/sys/net/netfilter/nf_conntrack_max: permission denied`，那就设置`echo "net.netfilter.nf_conntrack_max = 524288" | sudo tee -a /etc/sysctl.conf`，然后再执行`sysctl -p`
    
      7.5 如果报错没有权限修改nf_conntrack_max，则主机命令行执行 `echo "net.netfilter.nf_conntrack_max = 524288" | sudo tee -a /etc/sysctl.conf  && sysctl -p`
```
        sudo sysctl -w fs.inotify.max_user_watches=2099999999
        sudo sysctl -w fs.inotify.max_user_instances=2099999999
        sudo sysctl -w fs.inotify.max_queued_events=2099999999
  ```


# 5. 部署k8s集群

部署完rancher server后，进去rancher server的https://xx.xx.xx.xx/ 的web界面，这里的xx取决于你服务器的IP地址。

选择“Set a specific password to use”来配置rancher的密码，不选择"Allow collection of anonymous statistics ......"，选择"I agree to the terms and conditions ......"。

![在这里插入图片描述](https://cube-studio.oss-cn-hangzhou.aliyuncs.com/docs/csdn_image/ecda7c7b8861482091848e3b7fe22688.png)

之后选择添加集群->选择自定义集群->填写集群名称，集群名称英文小写
![在这里插入图片描述](https://cube-studio.oss-cn-hangzhou.aliyuncs.com/docs/csdn_image/ec25233e26a749d5bcb62a339e222163.jpeg)

![在这里插入图片描述](https://cube-studio.oss-cn-hangzhou.aliyuncs.com/docs/csdn_image/8ad63ad0bafb46268401f07ec2433cb6.jpeg)

然后选择kubernetes的版本（注意：这个版本在第一次打开选择页面时可能刷新不出来，需要等待1~2分钟再刷新才能显示）

注意：选择1.25版本的k8s。

![在这里插入图片描述](https://cube-studio.oss-cn-hangzhou.aliyuncs.com/docs/csdn_image/d60704f5dcf242b883a6dece66e07e93.jpeg)

![在这里插入图片描述](https://cube-studio.oss-cn-hangzhou.aliyuncs.com/docs/csdn_image/d778f141f20842b3ac2442acd75b66b5.jpeg)

修改Advanced option，主要是禁用nginx ingress，修改端口范围，使用docker info检查服务器上的docker根目录是否和默认的一致，不一致则需要更改。

之后选择编辑yaml文件。 添加kubelet的挂载参数，需要把分布式存储的位置都加入挂载。

```bash
    kube-api:
      ...
    kubelet:
      extra_args:
        # 与apiserver会话时的并发数，默认是10
        kube-api-burst: "30"
        # kubelet默认一次拉取一个镜像，设置为false可以同时拉取多个镜像，
        # 前提是存储驱动要为overlay2，对应的Dokcer也需要增加下载并发数，参考[docker配置](/rancher2x/install-prepare/best-practices/docker/)
        serialize-image-pulls: "false"
        # 节点资源预留
        enforce-node-allocatable: "pods"
        system-reserved: "cpu=0.25,memory=200Mi"
        kube-reserved: "cpu=0.25,memory=1500Mi"
        # docker存储不能和根目录是同一个分区才生效
        image-gc-high-threshold: 95
        image-gc-low-threshold: 90
        eviction-hard: "imagefs.available<5%,nodefs.available<5%,nodefs.inodesFree<5%"
        # 不限制最大并行拉取次数
        registry-qps: 0
        registry-burst: 10
        
      extra_binds:
        - '/data:/data'
        
```
![在这里插入图片描述](https://cube-studio.oss-cn-hangzhou.aliyuncs.com/docs/csdn_image/a380de5081d74bd5ac49f0392e6aa341.jpeg)

这个yaml文件中控制着k8s基础组件的启动方式。比如kubelet的启动参数，api-server的启动参数等等。

有几个需要修改的是k8s使用的网段，由于默认使用的是10.xx，如果和你公司的网段重复，则可以修改为其他网关，例如：
172.16.0.0/16和172.17.0.0/16 两个网段

services部分的示例（注意缩进对齐）

```bash
  services:
    etcd:
      backup_config:
        enabled: true
        interval_hours: 12
        retention: 6
        safe_timestamp: false
      creation: 12h
      extra_args:
        election-timeout: '5000'
        heartbeat-interval: '500'
      gid: 0
      retention: 72h
      snapshot: false
      uid: 0
    kube-api:
      always_pull_images: false
      pod_security_policy: false
      # 服务node port范围
      service_node_port_range: 10-32767
      # 服务的ip范围，如果公司ip网段与k8s网段有冲突，则需要改这里
      service_cluster_ip_range: 172.16.0.0/16
      # 证书 https版本isito需要，k8s在1.21版本以下的，需要加extra_args
      extra_args:     
        service-account-issuer: kubernetes.default.svc
        service-account-signing-key-file: /etc/kubernetes/ssl/kube-service-account-token-key.pem
    kube-controller:
      # 集群pod的ip范围，如果公司ip网段与k8s网段有冲突，则需要改这里
      cluster_cidr: 172.17.0.0/16
      # 集群服务的 ip 范围，如果公司ip网段与k8s网段有冲突，则需要改这里
      service_cluster_ip_range: 172.16.0.0/16
    kubelet:
      # dns服务的ip，如果公司ip网段与k8s网段有冲突，则需要改这里
      cluster_dns_server: 172.16.0.10
      # 主机镜像回收触发门槛，如果机器空间小，可以把这两个参数调高
      extra_args:
        # 配置特殊的端口
        port: 10250  
        image-gc-high-threshold: 90
        image-gc-low-threshold: 85
        resolv-conf: "/etc/resolv-src.conf"
      # kubelet挂载主机目录，这样才能使用subpath，所有情况下部署都必加，且仅此处是必须要加的
      extra_binds:
        - '/data:/data'
        - '/etc/resolv-src.conf:/etc/resolv-src.conf'
    kubeproxy: {}
    scheduler: {}
```

如果有其他的参数需要后面修改，我们可以再在这里对yaml文件进行修改，然后升级集群。 

修改后直接进入下一步。

接着可以选择节点的角色：etcd是用来部署k8s的数据库，可以多个节点etcd。control相当于k8s的master，用来部署控制组件，可以在多个节点的部署k8s master节点，实现k8s高可用。worker相当于k8s的工作节点。

我们可以在部署rancher server的这台机器上，添加etcd/control角色。(如果你准备单机部署或者只是简单尝试，可以把所有角色都选上)

![在这里插入图片描述](https://cube-studio.oss-cn-hangzhou.aliyuncs.com/docs/csdn_image/e9f72ad20ac74afca6dfbe4980065d4a.jpeg)

最后复制页面中显示的命令，接着在rancher server的终端上粘贴命令，注意在粘贴命令后面加上参数 --node-name xx.xx.xx.xx    也就是加上服务器主机的内网ip地址。

粘贴后等待部署完成就行了。

![在这里插入图片描述](https://cube-studio.oss-cn-hangzhou.aliyuncs.com/docs/csdn_image/9c6f2fa9750749edb92a1f92e48824a7.jpeg)

部署完成后，集群的状态会变为"Active"，之后就可以下载kubeconfig文件，连接k8s集群了。

![在这里插入图片描述](https://cube-studio.oss-cn-hangzhou.aliyuncs.com/docs/csdn_image/618cfde682044b77b7103fc811d5060b.jpeg)

## 5.1 配置认证过期问题

因为rancher server的证书有效期是一年，在一年后，rancher server会报证书过期。因此，可以通过下面的方式，创建新的证书。

```bash
# 2.6.2版本的解决方法
sudo docker exec -it <container_id> sh -c "rm /var/lib/rancher/k3s/server/tls/dynamic-cert.json"
sudo docker exec -it <container_id> k3s kubectl --insecure-skip-tls-verify=true delete secret -n kube-system k3s-serving
sudo docker restart <container_id>

rancher server修复后，重启每台机器的canal的网络pod


# 之前版本的解决方法
docker stop $RANCHER_CONTAINER_NAME
docker start $RANCHER_CONTAINER_NAME 
docker exec -it $RANCHER_CONTAINER_NAME sh -c "rm /var/lib/rancher/k3s/server/tls/dynamic-cert.json" 
docker logs --tail 3 $RANCHER_CONTAINER_NAME 
# 将出现类似于以下的内容: 
# 2021/01/03 03:07:01 [INFO] Waiting for server to become available: Get https://localhost:6443/version?timeout=30s: x509: certificate signed by unknown authority 
# 2021/01/03 03:07:03 [INFO] Waiting for server to become available: Get https://localhost:6443/version?timeout=30s: x509: certificate signed by unknown authority 
# 2021/01/03 03:07:05 [INFO] Waiting for server to become available: Get https://localhost:6443/version?timeout=30s: x509: certificate signed by unknown authority 

docker stop $RANCHER_CONTAINER_NAME 
docker start $RANCHER_CONTAINER_NAME

rancher server修复后，重启每台机器的canal的网络pod

```

# 6. 部署完成后需要部分修正

 1、由于coredns在资源limits太小了，因此可以取消coredns的limits限制，不然dns会非常慢，整个集群都会缓慢

# 7. 机器扩容

现在k8s集群已经有了一个master节点，但还没有worker节点，或者想添加更多的master/worker节点就需要机器扩容了。

在集群主机界面，点击编辑集群，然后选择角色为worker（根据自己的需求选择角色）

之后复制命令到目标主机上运行，注意复制的命令后面多添加一个参数--node-name xx.xx.xx.xx，把新加机器的ip信息带进去，等待完成就可以了。

# 8. rancher/k8s 多用户

如果集群部署好了，需要添加多种权限类型的用户来管理，则可以使用rancher来实现k8s的rbac的多用户。

# 9. 客户端kubectl

如果你不会使用rancher界面或者不习惯使用rancher界面，可以使用kubectl或者kubernetes-dashboard。

点击Kubeconfig文件可以看到config的内容，通过内容可以看到，kube-apiserver可以使用rancher-server（端口443）的api接口，或者kube-apiserver（端口6443）的接口控制k8s集群。
由于6443端口在idc网络里面并不能暴露到外面，所以主要使用rancher-server的443端口代理k8s-apiserver的控制。
提示，如果你的rancher server 坏了，你可以在内网通过6443端口继续控制k8s集群。

下载安装不同系统办公电脑对应的kubectl，然后复制config到~/.kube/config文件夹，就可以通过命令访问k8s集群了。

# 10. kubernetes-dashboard
如果你喜欢用k8s-dashboard，可以自己安装dashboard。
可以参考这个：https://kuboard.cn/install/install-k8s-dashboard.html

这样我们就完成了k8s的部署。

# 11. 节点清理
当安装失败需要重新安装，或者需要彻底清理节点。由于清理过程比较麻烦，我们可以在rancher界面上把node删除，然后再去机器上执行reset_docker.sh，这样机器就恢复了部署前的状态。

如果web界面上删除不掉，我们也可以通过kubectl的命令  

```bash
kubectl delete node node12
```

# 12，重新创建rancher server （参考rancher server迁移）

修改端口，或者修改启动环境变量，等需要重新创建rancher server
```bash
export RANCHER_CONTAINER_TAG=v2.8.5
export RANCHER_CONTAINER_NAME=myrancher
export PASSWORD=cube-studio
docker stop $RANCHER_CONTAINER_NAME
docker create --volumes-from $RANCHER_CONTAINER_NAME --name rancher-data rancher/rancher:$RANCHER_CONTAINER_TAG
docker run --volumes-from rancher-data -v $PWD:/backup alpine tar zcvf /backup/rancher-data-backup-$RANCHER_VERSION-$DATE.tar.gz /var/lib/rancher
docker pull rancher/rancher:$RANCHER_CONTAINER_TAG
# 重新创建的命令自己按需修改
docker run -d --privileged --volumes-from rancher-data --restart=unless-stopped -p 443:443 --name=myrancher-new -e CATTLE_TLS_MIN_VERSION=1.2 -e AUDIT_LEVEL=3 -e CATTLE_BOOTSTRAP_PASSWORD=$PASSWORD rancher/rancher:$RANCHER_CONTAINER_TAG

如果修改了启动端口，要在全局设置里面修改server-url，然后关闭docker
# 停止 Docker 服务
sudo systemctl stop docker
sudo systemctl stop docker.socket
sudo systemctl stop containerd

进去share-mnt容器的主机目录下/var/lib/docker/containers/<container_id>/config.v2.json，将其中的server-url改为新端口号的
最后再重启 
sudo systemctl start containerd
sudo systemctl start docker.socket
sudo systemctl start docker

然后 docker inspect share-mnt 看看该容器的启动参数变化了没

然后k8s config文件就可以使用了，然后再修改  cattle-system 空间下面的secret cattle-credentials 中的url 和 deployment cattle-cluster-agent 和 daemonset cattle-node-agent，把环境变量中server-url 地址改了

然后docker ps -a |grep agent 查看所有的agent是否正常了。share-mnt容器正常就是会停止，看一下日志是否正常就ok
```

# 13. rancher server 节点迁移
我们可以实现将rancher server 节点迁移到另一台机器，以防止机器废弃后无法使用的情况。

首先，先在原机器上把数据压缩，不要关闭源集群rancher server 因为后面还要执行kubectl，这里的.tar.gz的文件名称以实际为准

```bash
export RANCHER_CONTAINER_TAG=v2.8.5
docker create --volumes-from myrancher-new --name rancher-data-new rancher/rancher:$RANCHER_CONTAINER_TAG
docker run --volumes-from rancher-data-new  -v $PWD:/backup alpine tar zcvf /backup/rancher-data-backup-20210101.tar.gz /var/lib/rancher

```

之后把tar.gz 文件复制到新的rancher server机器上,这里的.tar.gz的文件名称以实际为准
```
tar -zxvf rancher-data-backup-20210101.tar.gz && mv var/lib/rancher /var/lib/
```

接着在新机器上启动新的rancher server

```
sudo docker run -d --restart=unless-stopped -v /var/lib/rancher:/var/lib/rancher -p 443:443 --privileged --name=myrancher -e AUDIT_LEVEL=3 rancher/rancher:$rancher_version

注意以下几点：
1、新rancher server的web界面上要修改rancher server的url
2、打开地址 https://新rancher的ip/v3/clusters/源集群id/clusterregistrationtokens
例如：
https://100.116.64.86/v3/clusters/c-dfqxv/clusterregistrationtokens
3、在上面的界面上找到最新时间的 insecureCommand 的内容，之后curl --insecure -sfl过去
curl --insecure -sfL https://100.108.176.29/v3/import/d9jzxfz7tmbsnbhf22jbknzlbjcck7c2lzpzknw8t8sd7f6tvz448b.yaml | kubectl apply -f -
```

配置kubeconfig文件为原集群，执行上面的命令。这样旧rancher上的应用就会连接到新的rancher server；

等新集群正常以后，将新机器加入到k8s集群的etcd controller节点；

将老机器踢出集群；

至此完成


# 14. 总结

rancher使用**全部容器化**的形式来部署k8s集群，能大幅度降低k8s集群扩部署/缩容的门槛。
你可以使用rancher来扩缩容 etcd，k8s-master，k8s-worker。
k8s集群(包括etcd)的增删节点动作是由rancher server节点控制，由rancher agent来执行的。在新节点上通过运行rancher agent容器，来访问rancher server 获取要执行的部署命令,部署对应的k8s组件容器（包含kubelet，api-server，scheduler，controller等）。

rancher本身并不改变k8s的基础组件和工作原理，k8s的架构依然不变，只不过多了一个认证代理（auth proxy），也就是前面说的config文件中的rancher server中的接口。

