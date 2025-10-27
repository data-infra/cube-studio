import functools
import re

from flask_appbuilder import Model
from sqlalchemy.orm import relationship
import json
from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
from sqlalchemy import (
    Boolean,
    Text,
    Enum,
)
import numpy
import random
import copy
import urllib.parse
from myapp.models.helpers import AuditMixinNullable
from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
from myapp import app,db
from myapp.models.helpers import ImportMixin
from myapp.models.model_team import Project
import pysnooper
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from flask_appbuilder.models.decorators import renders
from flask import Markup,request,g
from myapp.models.base import MyappModelBase
import datetime
metadata = Model.metadata
conf = app.config
from myapp.utils import core
from myapp.utils.py import py_k8s

class Repository(Model,AuditMixinNullable,MyappModelBase):
    __tablename__ = 'repository'
    id = Column(Integer, primary_key=True,comment='id主键')
    name = Column(String(200), unique = True, nullable=False,comment='英文名')
    server = Column(String(200), nullable=False,comment='仓库地址')
    user = Column(String(100), nullable=False,comment='账户')
    password = Column(String(100), nullable=False,comment='密码')
    hubsecret = Column(String(100),comment='k8s secret名')

    @property
    def hubsecret_url(self):
        if g.user.is_admin():
            url = conf.get('K8S_DASHBOARD_CLUSTER', '') + f'#/secret/pipeline/{self.hubsecret}?namespace=pipeline'
            return Markup(f'<a target=_blank href="{url}">{self.hubsecret}</a>')
        else:
            return self.hubsecret

    def __repr__(self):
        return self.name

class Images(Model,AuditMixinNullable,MyappModelBase):
    __tablename__='images'
    id = Column(Integer, primary_key=True,comment='id主键')
    project_id = Column(Integer, ForeignKey('project.id'),comment='项目组id')
    project = relationship(
        "Project", foreign_keys=[project_id]
    )

    name = Column(String(500), nullable=False,comment='英文名')
    describe = Column(String(1000), nullable=False,comment='描述')
    repository_id = Column(Integer, ForeignKey('repository.id'),comment='仓库id')
    repository = relationship(
        "Repository", foreign_keys=[repository_id]
    )
    entrypoint=Column(String(2000),comment='入口点')
    dockerfile=Column(Text,comment='dockerfile')
    gitpath=Column(String(200),comment='git地址')


    @property
    def images_url(self):
        if self.gitpath:
            return Markup(f'<a href="{self.gitpath}">{self.name}</a>')
        return self.name

    def __repr__(self):
        return self.name



class Job_Template(Model,AuditMixinNullable,MyappModelBase):
    __tablename__='job_template'
    id = Column(Integer, primary_key=True,comment='id主键')
    project_id = Column(Integer, ForeignKey('project.id'),comment='项目组id')
    project = relationship(
        "Project", foreign_keys=[project_id]
    )
    name = Column(String(500), nullable=False,unique=True,comment='英文名')
    version = Column(Enum('Release','Alpha',name='version'),nullable=False,default='Release',comment='版本')
    images_id = Column(Integer, ForeignKey('images.id'),comment='镜像id')
    images = relationship(
        Images, foreign_keys=[images_id]
    )
    hostAliases = Column(Text,comment='域名映射')   # host文件
    describe = Column(String(500), nullable=False,comment='描述')
    workdir=Column(String(400),comment='工作目录')
    entrypoint=Column(String(2000),comment='入口点')
    args=Column(Text,comment='启动参数')
    env = Column(Text,comment='默认自带的环境变量')   #
    volume_mount = Column(String(2000),default='',comment='强制必须挂载')  #
    privileged = Column(Boolean, default=False,comment=' 是否启用特权模式')   #
    accounts = Column(String(100),comment='使用k8s账户')   #
    demo=Column(Text,comment='配置示例')
    expand = Column(Text(65536), default='{}',comment='扩展参数')


    def __repr__(self):
        return self.name   # +"(%s)"%self.version

    @property
    def args_html(self):
        return Markup('<pre><code>' + self.args + '</code></pre>')

    @property
    def demo_html(self):
        return Markup('<pre><code>' + self.demo + '</code></pre>')

    @property
    def expand_html(self):
        return Markup('<pre><code>' + self.expand + '</code></pre>')


    @property
    def name_title(self):
        return Markup(f'<a data-toggle="tooltip" rel="tooltip" title data-original-title="{self.describe}">{self.name}</a>')

    # import pysnooper
    # @pysnooper.snoop()
    def get_env(self,name,default=None):
        if self.env and name in self.env:
            envs = self.env.split('\n')
            for env in envs:
                if name in env:
                    return env[env.index('=')+1:].strip()
        else:
            return default

    def clone(self):
        return Job_Template(
            name=self.name,
            version=self.version,
            project_id=self.project_id,
            images_id=self.images_id,
            describe=self.describe,
            args=self.args,
            demo=self.demo,
            expand=self.expand,
            entrypoint=self.entrypoint,
            workdir=self.workdir,
            hostAliases=self.hostAliases,
            env=self.env,
            volume_mount=self.volume_mount,
            privileged=self.privileged,
            accounts=self.accounts
        )


class Pipeline(Model,ImportMixin,AuditMixinNullable,MyappModelBase):
    __tablename__ = 'pipeline'
    id = Column(Integer, primary_key=True,comment='id主键')
    name = Column(String(100),nullable=False,unique=True,comment='英文名')
    describe = Column(String(200),nullable=False,comment='描述')
    project_id = Column(Integer, ForeignKey('project.id'),nullable=False,comment='项目组id')
    project = relationship(
        "Project", foreign_keys=[project_id]
    )
    dag_json = Column(Text,nullable=False,default='{}',comment='上下游关系')
    namespace=Column(String(100),default='pipeline',comment='命名空间')
    global_env = Column(String(500),default='',comment='全局环境变量')
    schedule_type = Column(Enum('once', 'crontab',name='schedule_type'),nullable=False,default='once',comment='调度类型')
    cron_time = Column(String(100),comment='调度周期')        #
    cronjob_start_time = Column(String(300), default='',comment='定时调度补录起点')
    pipeline_file=Column(Text(655360),default='',comment='workflow yaml文件')
    pipeline_argo_id = Column(String(100),comment='argo workflow id')
    version_id = Column(String(100),comment='workflow version id')
    run_id = Column(String(100),comment='workflow run id')
    node_selector = Column(String(100), default='cpu=true,train=true',comment='机器选择器')
    image_pull_policy = Column(Enum('Always','IfNotPresent',name='image_pull_policy'),nullable=False,default='Always',comment='镜像拉取策略')
    parallelism = Column(Integer, nullable=False,default=1,comment='同一个pipeline，最大并行的task数目')  #
    alert_status = Column(String(100), default='Pending,Running,Succeeded,Failed,Terminated',comment=' 哪些状态会报警Pending,Running,Succeeded,Failed,Unknown,Waiting,Terminated')   #
    alert_user = Column(String(300), default='',comment='报警接收人')

    expand = Column(Text(65536),default='[]',comment='前端保留参数，用于记录编排样式')
    depends_on_past = Column(Boolean, default=False,comment='是否依赖过往实例')
    max_active_runs = Column(Integer, nullable=False,default=3,comment='最大同时运行的pipeline实例')   #
    expired_limit = Column(Integer, nullable=False, default=0,comment='过期保留个数，此数值有效时，会优先使用，覆盖max_active_runs的功能')  #
    parameter = Column(Text(65536), default='{}',comment='后端扩展参数')

    priority = Column(String(100), default='high', comment='优先级')  # giving priority to meeting high-priority resource needs
    type = Column(String(100),nullable=True,unique=False,default='',comment='任务流类型')

    def __repr__(self):
        return self.name

    @property
    def pipeline_url(self):
        pipeline_url="/pipeline_modelview/api/web/" +str(self.id)
        return Markup(f'<a target=_blank href="{pipeline_url}">{self.describe}</a>')

    @property
    def run_pipeline(self):
        pipeline_run_url = "/pipeline_modelview/api/run_pipeline/" +str(self.id)
        return Markup(f'<a target=_blank href="{pipeline_run_url}">run</a>')

    @property
    def status(self):
        workflow_name = self.pipeline_argo_id
        workflow = db.session.query(Workflow).filter_by(name=workflow_name).first()
        if workflow:
            return workflow.status
        return 'unknown'

    @property
    def log(self):
        if self.run_id:
            pipeline_url = "/pipeline_modelview/api/web/log/%s"%self.id
            return Markup(f'<a target=_blank href="{pipeline_url}">{__("日志")}</a>')
        else:
            return Markup(__('日志'))


    @property
    def pod(self):
        url = "/pipeline_modelview/api/web/pod/%s" % self.id
        return Markup(f'<a target=_blank href="{url}">pod</a>')



    @property
    def dag_json_html(self):
        dag_json = self.dag_json or '{}'
        return Markup('<pre><code>' + dag_json + '</code></pre>')


    @property
    def expand_html(self):
        return Markup('<pre><code>' + self.expand + '</code></pre>')

    @property
    def parameter_html(self):
        return Markup('<pre><code>' + self.parameter + '</code></pre>')


    @property
    def pipeline_file_html(self):
        pipeline_file = self.pipeline_file or ''
        return Markup('<pre><code>' + pipeline_file + '</code></pre>')

    # @property
    # def describe_html(self):
    #     return Markup('<pre><code>' + self.pipeline_file + '</code></pre>')

    def sort(self,tasks):
        dag_json = json.loads(self.fix_dag_json())
        # 获取根节点
        root_nodes = [key for key in dag_json if not dag_json[key].get('upstream',[])]
        tasks_dict = {task.name:task for task in tasks}

        # 生成下行链路图
        for task_name in dag_json:
            dag_json[task_name]['downstream'] = []
            for task_name1 in dag_json:
                if task_name in dag_json[task_name1].get("upstream", []):
                    dag_json[task_name]['downstream'].append(task_name1)

        sored_tasks = []
        while root_nodes:
            new_root_node=[]
            for root_node in root_nodes:
                if root_node not in sored_tasks:
                    sored_tasks.append(root_node)
                    down_nodes = dag_json[root_node]['downstream']
                    new_root_node+=down_nodes
            root_nodes = list(set(new_root_node))
        tasks = [tasks_dict[task_name] for task_name in sored_tasks]
        return tasks

    # 获取pipeline中的所有task, 按顺序排好序
    # @pysnooper.snoop()
    def get_tasks(self,dbsession=db.session):
        return dbsession.query(Task).filter_by(pipeline_id=self.id).all()


    # @pysnooper.snoop()
    def delete_old_task(self, dbsession=db.session):
        try:
            expand_tasks = json.loads(self.expand) if self.expand else []
            tasks = dbsession.query(Task).filter_by(pipeline_id=self.id).all()
            tasks_id = [int(expand_task['id']) for expand_task in expand_tasks if expand_task.get('id', '').isdecimal()]
            for task in tasks:
                if task.id not in tasks_id:
                    db.session.delete(task)
                    db.session.commit()
        except Exception as e:
            print(e)

    # 获取当期运行时workflow的数量
    def get_workflow(self):

        back_crds = []
        try:
            k8s_client = py_k8s.K8s(self.project.cluster.get('KUBECONFIG',''))
            crd_info = conf.get("CRD_INFO", {}).get('workflow', {})
            if crd_info:
                crds = k8s_client.get_crd(group=crd_info['group'], version=crd_info['version'],
                                          plural=crd_info['plural'], namespace=self.namespace,
                                          label_selector="pipeline-id=%s"%str(self.id))
                for crd in crds:
                    if crd.get('labels', '{}'):
                        labels = json.loads(crd['labels'])
                        if labels.get('pipeline-id', '') == str(self.id):
                            back_crds.append(crd)
            return back_crds
        except Exception as e:
            print(e)
        return back_crds

    # 这个dag可能不对，所以要根据真实task纠正一下
    def fix_dag_json(self,dbsession=db.session):
        if not self.dag_json:
            return "{}"
        dag = json.loads(self.dag_json)
        # 如果添加了task，但是没有保存pipeline，就自动创建dag
        if not dag:
            tasks = self.get_tasks(dbsession)
            if tasks:
                dag = {}
                for task in tasks:
                    dag[task.name] = {}
                dag_json = json.dumps(dag, indent=4, ensure_ascii=False)
                return dag_json
            else:
                return "{}"

        # 清理dag中不存在的task
        if dag:
            tasks = self.get_tasks(dbsession)
            all_task_names = [task.name for task in tasks]
            # 先把没有加入的task加入到dag
            for task in tasks:
                if task.name not in dag:
                    dag[task.name] = {}

            # 把已经删除了的task移除dag
            dag_back = copy.deepcopy(dag)
            for dag_task_name in dag_back:
                if dag_task_name not in all_task_names:
                    del dag[dag_task_name]

            # 将已经删除的task从其他task的上游依赖中删除
            for dag_task_name in dag:
                upstream_tasks = dag[dag_task_name]['upstream'] if 'upstream' in dag[dag_task_name] else []
                new_upstream_tasks = []
                for upstream_task in upstream_tasks:
                    if upstream_task in all_task_names:
                        new_upstream_tasks.append(upstream_task)

                dag[dag_task_name]['upstream'] = new_upstream_tasks



            # def get_downstream(dag):
            #     # 生成下行链路图
            #     for task_name in dag:
            #         dag[task_name]['downstream'] = []
            #         for task_name1 in dag:
            #             if task_name in dag[task_name1].get("upstream", []):
            #                 dag[task_name]['downstream'].append(task_name1)
            #     return dag
            #
            # dag = get_downstream(dag)
            dag_json = json.dumps(dag, indent=4, ensure_ascii=False)

            return dag_json

    # 自动聚焦到视图中央
    # @pysnooper.snoop()
    def fix_position(self):
        expand_tasks = json.loads(self.expand) if self.expand else []
        if not expand_tasks:
            expand_tasks = []
        x=[]
        y=[]
        for item in expand_tasks:
            if "position" in item:
                if item['position'].get('x',0):
                    x.append(int(item['position'].get('x',0)))
                    y.append(int(item['position'].get('y', 0)))
        x_dist=400- numpy.mean(x) if x else 0
        y_dist = 300 -numpy.mean(y) if y else 0
        for item in expand_tasks:
            if "position" in item:
                if item['position'].get('x', 0):
                    item['position']['x'] = int(item['position']['x'])+x_dist
                    item['position']['y'] = int(item['position']['y']) + y_dist

        return expand_tasks




    # 生成前端锁需要的扩展字段
    def fix_expand(self,dbsession=db.session):
        # 补充expand 的基本节点信息（节点和关系）
        tasks_src = self.get_tasks(dbsession)
        tasks = {}
        for task in tasks_src:
            tasks[str(task.id)] = task

        expand_tasks = json.loads(self.expand) if self.expand else []
        if not expand_tasks:
            expand_tasks=[]
        expand_copy = copy.deepcopy(expand_tasks)

        # 已经不存在的task要删掉
        for item in expand_copy:
            # 节点类型
            if "data" in item:
                if item['id'] not in tasks:
                    expand_tasks.remove(item)

            # 上下游关系类型
            else:
                # if item['source'] not in tasks or item['target'] not in tasks:
                expand_tasks.remove(item)   # 删除所有的上下游关系，后面全部重新

        # 增加新的task的位置
        for task_id in tasks:
            exist_index=-1
            for index,item in enumerate(expand_tasks):
                if "data" in item and item['id']==str(task_id):
                    exist_index=index
                    break
            # 如果后端有节点，但是前端没有节点信息，就增加一个
            if exist_index==-1:
                # if task_id not in expand_tasks:
                expand_tasks.append({
                    "id": str(task_id),
                    "type": "dataSet",
                    "position": {
                        "x": random.randint(100,1000),
                        "y": random.randint(100,1000)
                    },
                    "data": {
                        # "taskId": task_id,
                        # "taskName": tasks[task_id].name,
                        "info": {
                            "describe": tasks[task_id].job_template.describe
                        },
                        "name": tasks[task_id].name,
                        "label": tasks[task_id].label
                    }
                })
            else:
                expand_tasks[exist_index]['data']={
                    "info": {
                        "describe": tasks[task_id].job_template.describe
                    },
                    "name": tasks[task_id].name,
                    "label": tasks[task_id].label
                }

        # 重写所有task的上下游关系
        dag_json = json.loads(self.dag_json)
        for task_name in dag_json:
            upstreams = dag_json[task_name].get("upstream", [])
            if upstreams:
                for upstream_name in upstreams:
                    upstream_task_id = [task_id for task_id in tasks if tasks[task_id].name==upstream_name][0]
                    task_id = [task_id for task_id in tasks if tasks[task_id].name==task_name][0]
                    if upstream_task_id and task_id:
                        expand_tasks.append(
                            {
                                "source": str(upstream_task_id),
                                "arrowHeadType": 'arrow',
                                "target": str(task_id),
                                # "targetHandle": None,
                                "id": self.name + "__edge-%snull-%snull" % (upstream_task_id, task_id)
                            }
                        )
        return expand_tasks


    # @pysnooper.snoop()
    def clone(self):
        return Pipeline(
            name=self.name.replace('_','-'),
            project_id=self.project_id,
            dag_json=self.dag_json,
            describe=self.describe,
            namespace=self.namespace,
            global_env=self.global_env,
            schedule_type='once',
            cron_time=self.cron_time,
            pipeline_file='',
            pipeline_argo_id='',
            node_selector=self.node_selector,
            image_pull_policy=self.image_pull_policy,
            parallelism=self.parallelism,
            alert_status=self.alert_status,
            expand=self.expand,
            parameter=self.parameter
        )



class Task(Model,ImportMixin,AuditMixinNullable,MyappModelBase):
    __tablename__ = 'task'
    id = Column(Integer, primary_key=True,comment='id主键')
    name = Column(String(100), nullable=False,comment='英文名')
    label = Column(String(100), nullable=False,comment='中文名')   # 别名
    job_template_id = Column(Integer, ForeignKey('job_template.id'),comment='任务模板id')
    job_template = relationship(
        "Job_Template", foreign_keys=[job_template_id]
    )
    pipeline_id = Column(Integer, ForeignKey('pipeline.id'),comment='任务流id')
    pipeline = relationship(
        "Pipeline", foreign_keys=[pipeline_id]
    )
    namespace = Column(String(100), default='pipeline', comment='命名空间')
    working_dir = Column(String(1000),default='',comment='启动目录')
    command = Column(String(1000),default='',comment='启动命令')
    overwrite_entrypoint = Column(Boolean,default=False,comment='是否覆盖模板中的入口点')
    args = Column(Text,comment='任务启动参数')
    volume_mount = Column(String(2000),default='kubeflow-user-workspace(pvc):/mnt',comment='挂载')   #
    node_selector = Column(String(100),default='cpu=true,train=true',comment='机器选择器')   #
    resource_memory = Column(String(100),default='2G',comment='申请内存')
    resource_cpu = Column(String(100), default='2',comment='申请cpu')
    resource_gpu= Column(String(100), default='0',comment='申请gpu')
    resource_rdma = Column(String(100), default='0',comment='rdma的资源数量')  #
    timeout = Column(Integer, nullable=False,default=0,comment='超时')
    retry = Column(Integer, nullable=False,default=0,comment='重试次数')
    outputs = Column(Text,default='{}',comment='task的输出，会将输出复制到minio上 ')   #   {'prediction': '/output.txt'}
    monitoring = Column(Text,default='{}',comment='该任务的监控信息')  #
    expand = Column(Text(65536), default='',comment='扩展参数')
    skip = Column(Boolean,name='skip',default=False,comment='是否跳过',quote=True)  #
    export_parent = "pipeline"


    def __repr__(self):
        return self.name

    @property
    def debug(self):
        return Markup(f'<a target=_blank href="/task_modelview/api/debug/{self.id}">debug</a>')

    @property
    def run(self):
        return Markup(f'<a target=_blank href="/task_modelview/api/run/{self.id}">run</a>')

    @property
    def clear(self):
        return Markup(f'<a href="/task_modelview/api/clear/{self.id}">clear</a>')

    @property
    def log(self):
        return Markup(f'<a target=_blank href="/task_modelview/api/log/{self.id}">log</a>')

    def get_node_selector(self):
        project_node_selector = self.get_default_node_selector(self.pipeline.project.node_selector,self.resource_gpu,'train')
        gpu_type = core.get_gpu(self.resource_gpu)[1]
        if gpu_type:
            project_node_selector+=',gpu-type='+gpu_type
        return project_node_selector


    @property
    def args_html(self):
        return Markup('<pre><code>' + self.args + '</code></pre>')

    @property
    def expand_html(self):
        return Markup('<pre><code>' + self.expand + '</code></pre>')

    @property
    def monitoring_html(self):
        try:
            monitoring = json.loads(self.monitoring)
            monitoring['link']="http://"+self.pipeline.project.cluster.get('HOST', request.host).split('|')[-1]+conf.get('GRAFANA_TASK_PATH','')+monitoring.get('pod_name','')
            return Markup('<pre><code>' + json.dumps(monitoring,ensure_ascii=False,indent=4) + '</code></pre>')
        except Exception:
            return Markup('<pre><code> nothing </code></pre>')

    @property
    def job_args_demo(self):
        return Markup('<pre><code>' + self.job_template.demo + '</code></pre>')




    def clone(self):
        return Task(
            name=self.name.replace('_','-'),
            label=self.label,
            job_template_id=self.job_template_id,
            pipeline_id=self.pipeline_id,
            working_dir=self.working_dir,
            command=self.command,
            args=self.args,
            volume_mount=self.volume_mount,
            node_selector=self.node_selector,
            resource_memory=self.resource_memory,
            resource_cpu=self.resource_cpu,
            resource_gpu=self.resource_gpu,
            timeout=self.timeout,
            retry=self.retry,
            expand=self.expand
        )


# 每次上传运行
class RunHistory(Model,MyappModelBase):
    __tablename__ = "run"
    id = Column(Integer, primary_key=True,comment='id主键')
    pipeline_id = Column(Integer, ForeignKey('pipeline.id'),comment='任务流id')
    pipeline = relationship(
        "Pipeline", foreign_keys=[pipeline_id]
    )
    pipeline_file = Column(Text(655360), default='',comment='workflow yaml')
    pipeline_argo_id = Column(String(100),comment='任务流 argo id')   # 上传的pipeline id
    version_id = Column(String(100),comment='上传的版本号')        #
    experiment_id = Column(String(100),comment='实验id')
    run_id = Column(String(100),comment='run id')
    message = Column(Text, default='',comment='消息')
    created_on = Column(DateTime, default=datetime.datetime.now, nullable=False,comment='创建时间')
    execution_date=Column(String(200), nullable=False,comment='执行时间')
    status = Column(String(100),default='comed',comment='状态')   # commed表示已经到了该调度的时间，created表示已经发起了调度。注意操作前校验去重

    @property
    def create_time(self):
        if self.created_on:
            return self.created_on.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def status_url(self):
        if self.status=='comed':
            return self.status

        path = conf.get('MODEL_URLS', {}).get('workflow', '') + '?filter=' + urllib.parse.quote(json.dumps([{"key": "labels", "value": self.run_id}], ensure_ascii=False))
        return Markup(f'<a target=_blank href="{path}">{self.status}</a>')

    @property
    def creator(self):
        return self.pipeline.creator

    @property
    def pipeline_url(self):
        return Markup(f'<a target=_blank href="/pipeline_modelview/api/web/{self.pipeline.id}">{self.pipeline.describe}</a>')


class Crd:
    # __tablename__ = "crd"
    id = Column(Integer, primary_key=True,comment='id主键')
    name = Column(String(100),default='',comment='英文名')
    cluster = Column(String(100), default='',comment='k8s集群')
    namespace = Column(String(100), default='',comment='命名空间')
    create_time=Column(String(100), default='',comment='创建时间')
    change_time = Column(String(100), default='',comment='修改时间')

    status = Column(String(100), default='',comment='状态')
    annotations = Column(Text, default='',comment='注释')
    labels = Column(Text, default='',comment='标签')
    spec = Column(Text(655360), default='',comment='配置详情')
    status_more = Column(Text(), default='',comment='状态')
    username = Column(String(100), default='',comment='用户名')
    info_json = Column(Text, default='{}',comment='通知记录')
    add_row_time = Column(DateTime, default=datetime.datetime.now,comment='记录时间')
    # delete = Column(Boolean,default=False)
    foreign_key = Column(String(100), default='',comment='外键')

    @property
    def annotations_html(self):
        return Markup('<pre><code>' + self.annotations + '</code></pre>')

    @property
    def labels_html(self):
        return Markup('<pre><code>' + self.labels + '</code></pre>')

    @property
    def final_status(self):
        status='unknown'
        try:
            if self.status_more:
                status = json.loads(self.status_more).get('phase','unknown')
        except Exception as e:
            print(e)
        default='<svg t="1669360410529" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="6711" width="20" height="20"><path d="M937.984 741.376c-6.144 10.24-18.432 14.336-28.672 8.192-10.24-6.144-14.336-18.432-8.192-28.672 118.784-212.992 40.96-481.28-172.032-598.016-212.992-118.784-481.28-40.96-598.016 172.032s-40.96 481.28 172.032 598.016c153.6 86.016 339.968 69.632 479.232-32.768 8.192-6.144 22.528-4.096 28.672 4.096 6.144 8.192 4.096 22.528-4.096 28.672-151.552 112.64-356.352 129.024-522.24 36.864-233.472-129.024-317.44-421.888-188.416-653.312 129.024-233.472 421.888-317.44 653.312-188.416 233.472 126.976 317.44 419.84 188.416 653.312z m-647.168-243.712l190.464 169.984 282.624-303.104c8.192-8.192 20.48-8.192 28.672 0 8.192 8.192 8.192 20.48 0 28.672l-311.296 331.776-219.136-198.656c-8.192-8.192-8.192-20.48-2.048-28.672 8.192-8.192 20.48-8.192 30.72 0z" p-id="6712" fill="#dbdbdb"></path></svg>'
        status_icon={
            "Running":'<svg t="1669360051741" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="6304" width="20" height="20"><path d="M512 512m-512 0a512 512 0 1 0 1024 0 512 512 0 1 0-1024 0Z" fill="#52C41A" p-id="6305"></path><path d="M178.614857 557.860571a42.496 42.496 0 0 1 60.123429-60.050285l85.942857 87.625143a42.496 42.496 0 0 1-60.050286 60.123428L178.614857 557.860571z m561.005714-250.148571a42.496 42.496 0 1 1 65.097143 54.637714L394.459429 725.577143a42.496 42.496 0 0 1-65.097143-54.637714l410.112-363.373715z" fill="#FFFFFF" p-id="6306"></path></svg>',
            "Error":'<svg t="1669359973288" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="3503" width="20" height="20"><path d="M549.044706 512l166.189176-166.249412a26.383059 26.383059 0 0 0 0-36.98447 26.383059 26.383059 0 0 0-37.044706 0L512 475.015529l-166.249412-166.249411a26.383059 26.383059 0 0 0-36.98447 0 26.383059 26.383059 0 0 0 0 37.044706L475.015529 512l-166.249411 166.249412a26.383059 26.383059 0 0 0 0 36.98447 26.383059 26.383059 0 0 0 37.044706 0L512 548.984471l166.249412 166.249411a26.383059 26.383059 0 0 0 36.98447 0 26.383059 26.383059 0 0 0 0-37.044706L548.984471 512zM512 1024a512 512 0 1 1 0-1024 512 512 0 0 1 0 1024z" fill="#E84335" p-id="3504"></path></svg>',
            "Failed":'<svg t="1669359973288" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="3503" width="20" height="20"><path d="M549.044706 512l166.189176-166.249412a26.383059 26.383059 0 0 0 0-36.98447 26.383059 26.383059 0 0 0-37.044706 0L512 475.015529l-166.249412-166.249411a26.383059 26.383059 0 0 0-36.98447 0 26.383059 26.383059 0 0 0 0 37.044706L475.015529 512l-166.249411 166.249412a26.383059 26.383059 0 0 0 0 36.98447 26.383059 26.383059 0 0 0 37.044706 0L512 548.984471l166.249412 166.249411a26.383059 26.383059 0 0 0 36.98447 0 26.383059 26.383059 0 0 0 0-37.044706L548.984471 512zM512 1024a512 512 0 1 1 0-1024 512 512 0 0 1 0 1024z" fill="#E84335" p-id="3504"></path></svg>',
            'Succeeded':'<svg t="1669360077850" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="6508" width="20" height="20"><path d="M512 85.333333c235.648 0 426.666667 191.018667 426.666667 426.666667s-191.018667 426.666667-426.666667 426.666667S85.333333 747.648 85.333333 512 276.352 85.333333 512 85.333333z m-74.965333 550.4L346.453333 545.152a42.666667 42.666667 0 1 0-60.330666 60.330667l120.704 120.704a42.666667 42.666667 0 0 0 60.330666 0l301.653334-301.696a42.666667 42.666667 0 1 0-60.288-60.330667l-271.530667 271.488z" fill="#4e8508" p-id="6509"></path></svg>'
        }

        return Markup(f'<div style="display: flex; align-items: center;">{status_icon.get(status,default)}&nbsp;&nbsp;{status}</div>')

    @property
    def spec_html(self):
        return Markup('<pre><code>' + self.spec + '</code></pre>')

    @property
    def status_more_html(self):
        return Markup('<pre><code>' + self.status_more + '</code></pre>')

    @property
    def info_json_html(self):
        return Markup('<pre><code>' + self.info_json + '</code></pre>')

    @property
    def namespace_url(self):
        # user_roles = [role.name.lower() for role in list(g.user.roles)]
        # if "admin" in user_roles:
        url = conf.get('K8S_DASHBOARD_CLUSTER', '') + '#/search?namespace=%s&q=%s' % (self.namespace, self.name.replace('_', '-'))
        return Markup(f'<a target=_blank href="{url}">{self.namespace}</a>')

    @property
    def stop(self):
        return Markup(f'<a href="../stop/{self.id}">停止</a>')


class Workflow(Model,Crd,MyappModelBase):
    __tablename__ = 'workflow'

    @property
    def namespace_url(self):
        if self.pipeline:
            url = conf.get('K8S_DASHBOARD_CLUSTER', '') + '#/search?namespace=%s&q=%s' % (self.namespace, self.pipeline.name.replace('_', '-'))
            return Markup(f'<a target=_blank href="{url}">{self.namespace}</a>')
        else:
            url = conf.get('K8S_DASHBOARD_CLUSTER', '') + '#/search?namespace=%s&q=%s' % (self.namespace, self.name.replace('_', '-'))
            return Markup(f'<a target=_blank href="{url}">{self.namespace}</a>')

    @property
    def run_history(self):
        label = json.loads(self.labels) if self.labels else {}
        runid = label.get('run-id','')
        if runid:
            return db.session.query(RunHistory).filter(RunHistory.pipeline_file.contains(runid)).first()
            # return db.session.query(RunHistory).filter_by(run_id=runid).first()
        else:
            return None

    @property
    def schedule_type(self):
        run_history = self.run_history
        if run_history:
            return 'crontab'
        else:
            return 'once'


    @property
    def execution_date(self):
        run_history = self.run_history
        if run_history:
            return run_history.execution_date
        else:
            return 'once'

    # 每个任务的细节
    @property
    def task_status(self):
        status_more = json.loads(self.status_more)
        task_status={}
        nodes=status_more.get('nodes',{})
        tasks = self.pipeline.get_tasks()
        for node_name in nodes:
            node = nodes[node_name]
            if node['type']=='Pod':
                if node['phase']=='Succeeded':     # 那些重试和失败的都忽略掉
                    templateName=node['templateName']
                    for task in tasks:
                        if task.name==templateName:
                            finish_time = node['finishedAt']
                            finish_time = datetime.datetime.strptime(finish_time,f'%Y-%m-%d{"T" if "T" in finish_time else " "}%H:%M:%S{"Z" if "Z" in finish_time else ""}')
                            start_time = node['startedAt']
                            start_time = datetime.datetime.strptime(start_time,f'%Y-%m-%d{"T" if "T" in start_time else " "}%H:%M:%S{"Z" if "Z" in start_time else ""}')
                            elapsed = (finish_time - start_time).total_seconds() / 60 / 60
                            task_status[task.label]= str(round(elapsed,2))+"h"

        message=""
        for key in task_status:
            message += key+": "+task_status[key]+"\n"
        return Markup('<pre><code>' + message + '</code></pre>')



    @property
    def elapsed_time(self):
        try:
            status_mode = json.loads(self.status_more)
            finish_time=status_mode.get('finishedAt',self.change_time)
            if not finish_time:
                if self.status.lower() in ['running', 'pending', 'suspended']:
                    finish_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                else:
                    finish_time=self.change_time

            start_time = status_mode.get('startedAt', '')
            # print(finish_time,start_time)

            if finish_time and start_time:
                finish_time = datetime.datetime.strptime(finish_time, f'%Y-%m-%d{"T" if "T" in finish_time else " "}%H:%M:%S{"Z" if "Z" in finish_time else ""}')
                start_time = datetime.datetime.strptime(start_time, f'%Y-%m-%d{"T" if "T" in start_time else " "}%H:%M:%S{"Z" if "Z" in start_time else ""}')
                elapsed = (finish_time-start_time).total_seconds()/60/60
                return str(round(elapsed,2))+"h"
        except Exception as e:
            print(e)
        return 'unknown'


    @property
    def pipeline_url(self):
        if self.labels:
            try:
                labels = json.loads(self.labels)
                pipeline_id = labels.get("pipeline-id",'')
                if pipeline_id:
                    pipeline = db.session.query(Pipeline).filter_by(id=int(pipeline_id)).first()
                    if pipeline:
                        # return Markup(f'{pipeline.describe}')
                        return Markup(f'<a href="/pipeline_modelview/api/web/{pipeline.id}">{pipeline.describe}</a>')

                pipeline_name = self.name[:-6]
                pipeline = db.session.query(Pipeline).filter_by(name=pipeline_name).first()
                if pipeline:
                    return Markup(f'{pipeline.describe}')

            except Exception as e:
                print(e)
        return Markup('unknown')

    @property
    def pipeline(self):
        if self.labels:
            try:
                labels = json.loads(self.labels)
                pipeline_id = labels.get("pipeline-id",'')
                if pipeline_id:
                    pipeline = db.session.query(Pipeline).filter_by(id=int(pipeline_id)).first()
                    if pipeline:
                        return pipeline

                # pipeline_name = self.name[:-6]
                # pipeline = db.session.query(Pipeline).filter_by(name=pipeline_name).first()
                # return pipeline

            except Exception as e:
                print(e)
        return None


    @property
    def project(self):
        pipeline = self.pipeline
        if pipeline:
            return pipeline.project.name
        else:
            return "unknown"

    @property
    def log(self):
        url = f'/frontend/commonRelation?backurl=/workflow_modelview/api/web/dag/{self.cluster}/{self.namespace}/{self.name}'
        return Markup(f'<a target=_blank href="{url}">{__("日志")}</a>')


    @property
    def stop(self):
        if self.username == g.user.username or g.user.is_admin() or (self.pipeline and self.pipeline.project.user_role(g.user.id) == 'creator'):
            return Markup(f'<a href="/workflow_modelview/api/stop/{self.id}">{__("停止")}</a>')
        else:
            return __("停止")

