#!/bin/bash

set -ex

rm -f /home/myapp/myapp/static/mnt
mkdir -p /data/k8s/kubeflow/pipeline/workspace
ln -s /data/k8s/kubeflow/pipeline/workspace /home/myapp/myapp/static/mnt

rm -f /home/myapp/myapp/static/dataset
mkdir -p /data/k8s/kubeflow/dataset
ln -s /data/k8s/kubeflow/dataset /home/myapp/myapp/static/

rm -f /home/myapp/myapp/static/aihub
ln -s /cube-studio/aihub /home/myapp/myapp/static/

rm -f /home/myapp/myapp/static/global
ln -s /data/k8s/kubeflow/global /home/myapp/myapp/static/
export FLASK_APP=myapp:app
python myapp/create_db.py
# myapp db init    # 生成migrations文件夹，不再需要操作
# myapp db migrate   # 生成对应版本数据库表的升级文件到versions文件夹下，需要你的数据库是已经upgrade的
myapp db upgrade     # 数据库表同步更新到mysql
# 创建admin相关的用户，权限，角色，视图
myapp fab create-admin --username admin --firstname admin --lastname admin --email admin@tencent.com --password admin
# 会创建默认的角色和权限。会创建自定义的menu权限，也才能显示自定义menu。
myapp init

if [ "$STAGE" = "build" ]; then
  # 构建前端主体
  cd /home/myapp/myapp/frontend && npm install && npm run build
  # 构建机器学习pipeline
  cd /home/myapp/myapp/vision && npm install && npm run build
  # 构建数据ETL pipeline
  cd /home/myapp/myapp/visionPlus && yarn && npm run build
elif [ "$STAGE" = "dev" ]; then
  export FLASK_APP=myapp:app
#  FLASK_ENV=development  flask run -p 80 --with-threads  --host=0.0.0.0
  python myapp/check_tables.py
  python myapp/run.py

elif [ "$STAGE" = "prod" ]; then
  export FLASK_APP=myapp:app
  python myapp/check_tables.py
  # 默认worker数量为20
  WORKERS_NUMS=20
  # 根据是否配置了pod的resource.limits.cpu资源动态调整workers的数量
  if [[ $(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us) -ne -1 ]]; then
    # IO密集型，worker数量等于resource.limits.cpu核心数量*2+1，如果分配小于一个核心，等于1
    WORKERS_NUMS=$(($(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us)/$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us)*2+1))
  fi
  # gunicorn方式启动，将错误与访问日志输出到容终端
  gunicorn --bind  0.0.0.0:80 --workers ${WORKERS_NUMS} --worker-class=gevent --timeout 300 --limit-request-line 0 --limit-request-field_size 0 --access-logfile=- --error-logfile=- --log-level=info myapp:app
else
    myapp --help
fi


