from flask_appbuilder.baseviews import expose_api
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from myapp.views.baseSQLA import MyappSQLAInterface as SQLAInterface
from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
from flask_appbuilder.forms import GeneralModelConverter
from wtforms.validators import DataRequired, Regexp
from myapp.models.model_job import Repository
from myapp import app, appbuilder, db
from myapp.models.model_job import Repository
from wtforms import StringField
from myapp.views.view_team import Project_Join_Filter, filter_join_org_project
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget
from myapp.forms import MyBS3TextAreaFieldWidget, MySelect2Widget
import pysnooper
from .baseApi import MyappModelRestApi
from flask import (
    flash,
    g,
    Markup,
    redirect, render_template
)
from .base import (
    DeleteMixin,
    MyappFilter,
    MyappModelView,
)
from flask_appbuilder import expose
import datetime, time, json

from ..models.model_team import Project

conf = app.config

from myapp.models.model_docker import Docker


class Docker_Filter(MyappFilter):
    # @pysnooper.snoop()
    def apply(self, query, func):
        if g.user.is_admin():
            return query

        return query.filter(self.model.created_by_fk == g.user.id)


class Docker_ModelView_Base():
    datamodel = SQLAInterface(Docker)
    label_title = _("容器")

    crd_name = 'docker'

    conv = GeneralModelConverter(datamodel)
    base_permissions = ['can_add', 'can_delete', 'can_edit', 'can_list', 'can_show']
    base_order = ('changed_on', 'desc')
    base_filters = [["id", Docker_Filter, lambda: []]]
    order_columns = ['id']
    add_columns = ['project', 'describe', 'base_image', 'target_image',  'consecutive_build','expand']
    edit_columns = add_columns
    search_columns = ['created_by', 'project']
    list_columns = ['project', 'describe', 'consecutive_build', 'image_history', 'debug']
    fixed_columns = ['debug']
    cols_width = {
        "project": {"type": "ellip2", "width": 150},
        "describe": {"type": "ellip2", "width": 200},
        "image_history": {"type": "ellip3", "width": 600},
        "debug": {"type": "ellip2", "width": 120}
    }

    add_form_query_rel_fields = {
        "project": [["name", Project_Join_Filter, 'org']]
    }
    edit_form_query_rel_fields = add_form_query_rel_fields
    expand = {
        "volume_mount": "kubeflow-user-workspace(pvc):/mnt",
        "resource_memory": "8G",
        "resource_cpu": "4"
    }
    expand_columns={
        "expand":{
            # 'volume_mount': StringField(
            #     label= _('挂载'),
            #     default='kubeflow-user-workspace(pvc):/mnt/',
            #     description= _('外部挂载，格式:<br>$pvc_name1(pvc):/$container_path1,$hostpath1(hostpath):/$container_path2<br>注意pvc会自动挂载对应目录下的个人username子目录'),
            #     widget=BS3TextFieldWidget(),
            #     validators=[Regexp('^[\x00-\x7F]*$')]
            # ),
            'resource_memory': StringField(
                label= _('内存'),
                default='8G',
                description= _('内存的资源使用配置，示例：1G，20G'),
                widget=BS3TextFieldWidget(),
                validators=[DataRequired(), Regexp("^[0-9]*G$")]
            ),
            'resource_cpu': StringField(
                label= _('cpu'),
                default='4',
                description= _('cpu的资源使用配置(单位：核)，示例：2'),
                widget=BS3TextFieldWidget(),
                validators=[DataRequired(),Regexp("^[0-9]*$")]
            ),
            'resource_gpu': StringField(
                label= _('gpu'),
                default='0',
                description= _('申请的gpu卡数目，示例:2，每个容器独占整卡。-1为共享占用方式，小数(0.1)为vgpu方式，申请具体的卡型号，可以类似 1(V100)'),
                widget=BS3TextFieldWidget(),
                validators=[DataRequired(),Regexp('^[\-\.0-9,a-zA-Z\(\)]*$')]
            )
        }
    }
    add_form_extra_fields = {
        "describe": StringField(
            _("描述"),
            default='',
            description= _("目标镜像描述"),
            widget=BS3TextFieldWidget(),
            validators=[DataRequired()]
        ),

        "expand": StringField(
            _('扩展'),
            default=json.dumps(expand, ensure_ascii=False, indent=4),
            description='',
            widget=MyBS3TextAreaFieldWidget(rows=3)
        )

    }
    edit_form_extra_fields = add_form_extra_fields

    # @pysnooper.snoop()
    def pre_add_web(self, docker=None):
        # self.add_form_extra_fields['project'] = QuerySelectField(
        #     _('项目组'),
        #     default='',
        #     description=_('部署项目组，在切换项目组前注意先停止当前容器'),
        #     query_factory=filter_join_org_project,
        #     widget=MySelect2Widget(extra_classes="readonly" if docker else None, new_web=False),
        # )
        self.add_form_extra_fields['target_image'] = StringField(
            _('目标镜像'),
            default=conf.get('PUSH_REPOSITORY_ORG','ccr.ccs.tencentyun.com/cube-studio/')+g.user.username+":"+datetime.datetime.now().strftime('%Y.%m.%d'+".1"),
            description= _("目标镜像名，将直接推送到目标仓库，需在镜像仓库中配置了相应仓库的账号密码"),
            widget=BS3TextFieldWidget(),
            validators=[DataRequired(),Regexp('^[a-zA-Z0-9\-._:@\/]*$')]
        )
        self.add_form_extra_fields['base_image'] = StringField(
            _('基础镜像'),
            default=conf.get('USER_IMAGE',''),
            description=f'{__("基础镜像和构建方法可参考：")}<a target="_blank" href="%s">{__("点击打开")}</a>' % (conf.get('HELP_URL',{}).get('docker', '')),
            widget=BS3TextFieldWidget(),
            validators=[DataRequired(), Regexp('^[a-zA-Z0-9\-._:@\/]*$')]
        )
        # # if g.user.is_admin():
        # self.edit_columns=['describe','base_image','target_image','need_gpu','consecutive_build']
        self.edit_form_extra_fields = self.add_form_extra_fields

        self.default_filter = {
            "created_by": g.user.id
        }


    pre_update_web = pre_add_web

    def pre_add(self, item):
        if '/' not in item.target_image:
            flash(__('目标镜像名称不符合规范，未发现目标所属仓库的配置'), 'warning')
        else:
            repository_host = item.target_image[:item.target_image.index('/')]
            repository = db.session.query(Repository).filter(Repository.server.contains(repository_host)).first()
            if not repository:
                flash(__('目标镜像名称不符合规范，未发现目标所属仓库的配置'), 'warning')

        # image_org=conf.get('REPOSITORY_ORG')+g.user.username+":"
        # if image_org not in item.target_image or item.target_image==image_org:
        #     flash('目标镜像名称不符合规范','warning')

        if not item.namespace:
            item.namespace = item.project.notebook_namespace
        if item.expand:
            expand = json.loads(item.expand)
            expand['namespace'] = json.loads(item.project.expand).get('NOTEBOOK_NAMESPACE', conf.get('NOTEBOOK_NAMESPACE','jupyter'))
            item.expand = json.dumps(expand,indent=4,ensure_ascii=False)

    def pre_update(self, item):
        self.pre_add(item)
        # 如果修改了基础镜像，就把debug中的任务删除掉
        if self.src_item_json:
            # k8s集群更换了，要删除原来的
            if str(self.src_item_json.get('project_id', '1'))!=str(item.project.id):
                src_project = db.session.query(Project).filter_by(id=int(self.src_item_json.get('project_id', '1'))).first()
                if src_project and src_project.cluster['NAME']!=item.project.cluster['NAME']:
                    self.delete_pod(item.id,src_project.cluster['NAME'])
                    flash(__('发现集群更换，已帮你删除之前启动的debug容器'), 'success')
            elif item.base_image != self.src_item_json.get('base_image', ''):
                self.delete_pod(item.id)
                item.last_image = ''
                flash(__('发现基础镜像更换，已帮你删除之前启动的debug容器'), 'success')

    # @event_logger.log_this
    @expose_api(description="容器debug",url="/debug/<docker_id>", methods=["GET", "POST"])
    # @pysnooper.snoop()
    def debug(self, docker_id):
        docker = db.session.query(Docker).filter_by(id=docker_id).first()

        from myapp.utils.py.py_k8s import K8s
        k8s_client = K8s(docker.project.cluster.get('KUBECONFIG', ''))
        namespace = docker.project.notebook_namespace
        pod_name = "docker-%s-%s" % (docker.created_by.username, str(docker.id))
        pod = k8s_client.get_pods(namespace=namespace, pod_name=pod_name)
        if pod:
            pod = pod[0]
        # 有历史非运行态，直接删除
        # if pod and (pod['status']!='Running' and pod['status']!='Pending'):
        if pod and pod['status'] == 'Succeeded':
            k8s_client.delete_pods(namespace=namespace, pod_name=pod_name)
            time.sleep(2)
            pod = None

        # 没有历史或者没有运行态，直接创建
        if not pod or (pod['status']!='Running' and pod['status']!='Pending'):

            command=['sh','-c','sleep 7200 && hour=`date +%H` && while [ $hour -ge 06 ];do sleep 3600;hour=`date +%H`;done']
            hostAliases = conf.get('HOSTALIASES')

            default_volume_mount = docker.project.volume_mount
            image_pull_secrets = conf.get('HUBSECRET', [])
            user_repositorys = db.session.query(Repository).filter(Repository.created_by_fk == g.user.id).all()
            image_pull_secrets = list(set(image_pull_secrets + [rep.hubsecret for rep in user_repositorys]))
            docker.namespace = namespace
            db.session.commit()
            k8s_client.create_debug_pod(namespace,
                                        name=pod_name,
                                        command=command,
                                        labels={"app": "docker", "user": g.user.username, "pod-type": "docker"},
                                        annotations={'project':docker.project.name},
                                        args=None,
                                        volume_mount=json.loads(docker.expand).get('volume_mount',default_volume_mount) if docker.expand else default_volume_mount,
                                        working_dir='/mnt/%s'%docker.created_by.username,
                                        node_selector='train=true,org=%s'%(docker.project.org,),
                                        resource_memory="0~"+json.loads(docker.expand).get('resource_memory','8G') if docker.expand else '8G',
                                        resource_cpu='0~'+json.loads(docker.expand).get('resource_cpu','4') if docker.expand else '4',
                                        resource_gpu=json.loads(docker.expand if docker.expand else '{}').get('resource_gpu','0'),
                                        image_pull_policy=conf.get('IMAGE_PULL_POLICY','Always'),
                                        image_pull_secrets=image_pull_secrets,
                                        image= docker.last_image if docker.last_image and docker.consecutive_build else docker.base_image,
                                        hostAliases=hostAliases,
                                        env={
                                            "USERNAME": docker.created_by.username
                                        },
                                        privileged=None,
                                        accounts=None,
                                        username=docker.created_by.username)

        try_num = 20
        while (try_num > 0):
            pod = k8s_client.get_pods(namespace=namespace, pod_name=pod_name)
            # print(pod)
            if pod:
                pod = pod[0]
            # 有历史非运行态，直接删除
            if pod and pod['status'] == 'Running':
                break
            try_num = try_num - 1
            time.sleep(2)
        if try_num == 0:
            pod_url = f'/web/search/{docker.project.cluster["NAME"]}/{namespace}/{pod_name}'
            # event = k8s_client.get_pod_event(namespace=namespace,pod_name=pod_name)

            message = __('拉取镜像时间过长，一分钟后刷新此页面，或者打开链接：')+'<a href="%s">' % pod_url+__('查看pod信息')+'</a>'
            flash(message, 'warning')
            return message, 400
            # return self.response(400, message)
            # return self.response(400,**{"message":message,"status":1,"result":pod['status_more']})
            # return redirect(conf.get('MODEL_URLS',{}).get('docker',''))

        flash(__('镜像调试只安装环境，请不要运行业务代码。当晚前请注意保存镜像'), 'warning')
        return redirect(f'/k8s/web/debug/{docker.project.cluster["NAME"]}/{namespace}/{pod_name}/{pod_name}')

    # @event_logger.log_this
    @expose_api(description="清理在线调试镜像",url="/delete_pod/<docker_id>", methods=["GET", "POST"])
    # @pysnooper.snoop()
    def delete_pod(self, docker_id,cluster=None):
        docker = db.session.query(Docker).filter_by(id=docker_id).first()
        from myapp.utils.py.py_k8s import K8s
        if not cluster:
            cluster = docker.project.cluster['NAME']
        k8s_client = K8s(conf.get('CLUSTERS').get(cluster).get('KUBECONFIG', ''))
        namespace = docker.namespace
        pod_name = "docker-%s-%s" % (docker.created_by.username, str(docker.id))
        k8s_client.delete_pods(namespace=namespace, pod_name=pod_name)
        pod_name = "docker-commit-%s-%s" % (docker.created_by.username, str(docker.id))
        k8s_client.delete_pods(namespace=namespace, pod_name=pod_name)
        flash(__('清理结束，可重新进行调试'), 'success')
        return redirect(conf.get('MODEL_URLS', {}).get('docker', ''))

    def pre_delete(self,item):
        self.delete_pod(docker_id=item.id)

    # @event_logger.log_this
    @expose_api(description="保存在线调试镜像",url="/save/<docker_id>", methods=["GET", "POST"])
    # @pysnooper.snoop(watch_explode='status')
    def save(self, docker_id):
        docker = db.session.query(Docker).filter_by(id=docker_id).first()
        from myapp.utils.py.py_k8s import K8s
        k8s_client = K8s(docker.project.cluster.get('KUBECONFIG', ''))
        namespace = docker.namespace
        pod_name = "docker-%s-%s" % (docker.created_by.username, str(docker.id))
        pod = None
        try:
            pod = k8s_client.v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        except Exception as e:
            pass
        node_name = ''
        container_id = ''
        if pod:
            node_name = pod.spec.node_name
            containers = [container for container in pod.status.container_statuses if container.name == pod_name]
            if containers:
                container_id = containers[0].container_id.replace('docker://', '').replace('containerd://','')

        if not node_name or not container_id:
            message = __('没有发现正在运行的调试镜像，请先调试镜像，安装环境后，再保存生成新镜像')
            flash(message, category='warning')
            # return self.response(400, **{"message": message, "status": 1, "result": {}})
            return redirect(conf.get('MODEL_URLS',{}).get('docker',''))

        # flash('新镜像正在保存推送中，请留意消息通知',category='success')
        # return redirect(conf.get('MODEL_URLS',{}).get('docker',''))

        pod_name = "docker-commit-%s-%s" % (docker.created_by.username, str(docker.id))
        login_command = ''
        all_repositorys = db.session.query(Repository).all()
        # 这里可能有同一个服务器下面的多个仓库，同一个仓库名，也可以配置了多个账号。
        all_repositorys = [repo for repo in all_repositorys if repo.server in docker.target_image]
        # 如果未发现合适的仓库
        if not all_repositorys:
            flash(__('构建推送镜像前，请先添加镜像仓库信息')+docker.target_image[:docker.target_image.index('/')],'warning')
            return redirect(conf.get('MODEL_URLS', {}).get('repository'))
        repo = max(all_repositorys, key=lambda repo: len(repo.server)+1000*int(repo.created_by.username==g.user.username))  # 优先使用自己创建的，再使用最匹配的，最后使用别人创建的
        cli = conf.get('CONTAINER_CLI','docker')

        if repo:
            server = repo.server[:repo.server.index('/')] if '/' in repo.server else repo.server
            login_command = f'{cli} login --username {repo.user} --password {repo.password} {server}'

        if cli=='nerdctl':
            cli = 'nerdctl --namespace k8s.io'
        if login_command:
            command = ['sh', '-c', f'{login_command} && {cli} commit {container_id} {docker.target_image} && {cli} push {docker.target_image}']
        else:
            command = ['sh', '-c', f'{cli} commit {container_id} {docker.target_image} && {cli} push {docker.target_image}']

        hostAliases = conf.get('HOSTALIASES')

        image_pull_secrets = conf.get('HUBSECRET', [])
        user_repositorys = db.session.query(Repository).filter(Repository.created_by_fk==g.user.id).all()
        image_pull_secrets = list(set(image_pull_secrets+ [rep.hubsecret for rep in user_repositorys]))

        k8s_client.create_debug_pod(
            namespace=namespace,
            name=pod_name,
            command=command,
            labels={"app": "docker", "user": g.user.username, "pod-type": "docker"},
            annotations={'project': docker.project.name},
            args=None,
            volume_mount=conf.get('DOCKER_SOCKET','/var/run/docker.sock(hostpath):/var/run/docker.sock') if 'docker' in cli else conf.get('CONTAINERD_SOCKET','/etc/containerd/(hostpath):/etc/containerd/,/run/containerd/containerd.sock(hostpath):/run/containerd/containerd.sock'),
            working_dir='/mnt/%s' % docker.created_by.username,
            node_selector=None,
            resource_memory='0~10G',
            resource_cpu='0~10',
            resource_gpu='0',
            image_pull_policy='IfNotPresent',
            image_pull_secrets=image_pull_secrets,
            image=conf.get('NERDCTL_IMAGES', f'{cli}:xx') if cli!='docker' else conf.get('DOCKER_IMAGES', f'{cli}:xx'),
            hostAliases=hostAliases,
            env={
                "USERNAME": docker.created_by.username
            },
            privileged=True,
            accounts=None,
            username=docker.created_by.username,
            node_name=node_name
        )
        from myapp.tasks.async_task import check_docker_commit
        # 发起异步任务检查commit pod是否完成，如果完成，修正last_image
        kwargs = {
            "docker_id": docker.id
        }
        check_docker_commit.apply_async(kwargs=kwargs)

        return redirect("/k8s/web/log/%s/%s/%s" % (docker.project.cluster.get('NAME', ''), namespace, pod_name))


    @expose_api(description="创建在线调试镜像",url='/entry/docker', methods=['GET', 'DELETE'])
    def entry_docker(self):
        return redirect('/frontend/dev/images/docker?isVisableAdd=true')

# 添加api
class Docker_ModelView_Api(Docker_ModelView_Base, MyappModelRestApi):
    datamodel = SQLAInterface(Docker)
    route_base = '/docker_modelview/api'



appbuilder.add_api(Docker_ModelView_Api)
