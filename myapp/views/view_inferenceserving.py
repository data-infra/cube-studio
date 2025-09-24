import math
import random
import threading
import uuid
from flask import Flask, request, Response
import requests
from flask_appbuilder.baseviews import expose_api

from myapp.views.baseSQLA import MyappSQLAInterface as SQLAInterface
from flask import jsonify, render_template
from jinja2 import Environment, BaseLoader, DebugUndefined
from myapp.models.model_serving import InferenceService
from myapp.utils import core
from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
from flask_appbuilder.actions import action
from myapp import app, appbuilder, db
import re
from kubernetes.client import ApiException
import pytz
import pysnooper
import copy
from sqlalchemy.exc import InvalidRequestError
from myapp.models.model_job import Repository
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from myapp import security_manager
from wtforms.validators import DataRequired, Length, Regexp
from wtforms import SelectField, StringField
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget, Select2ManyWidget, Select2Widget
from myapp.forms import MyBS3TextAreaFieldWidget, MySelect2Widget, MyBS3TextFieldWidget, MySelectMultipleField
from myapp.views.view_team import Project_Join_Filter, filter_join_org_project
from flask import (
    flash,
    g,
    Markup,
    redirect,
    request
)
from .base import (
    MyappFilter,
    MyappModelView,

)
from .baseApi import (
    MyappModelRestApi
)

from flask_appbuilder import expose
import datetime, time, json

conf = app.config

# 推理服务的各种配置

INFERNENCE_MODEL_PATH = {
    "ml-server": "/mnt/.../$model_name.pkl",
    "tfserving": "/mnt/.../saved_model",
    "torch-server": "/mnt/.../$model_name.mar",
    "triton-server": "onnx:/mnt/.../model.onnx(model.plan,model.bin,model.savedmodel/,model.pt,model.dali)"
}


# 推理服务的各种配置
INFERNENCE_HOST={
    "tfserving":"/v1/models/$model_name/metadata",
    "torch-server":":8081/models",
    "triton-server":'/v2/models/$model_name'
}

INFERNENCE_CONFIGMAP={
}
INFERNENCE_COMMAND={
    "tfserving":"/usr/bin/tf_serving_entrypoint.sh --model_config_file=/config/models.config --monitoring_config_file=/config/monitoring.config --platform_config_file=/config/platform.config --rest_api_num_threads=300 --enable_batching=true",
    "torch-server":"torchserve --start --model-store /models/$model_name/ --models $model_name=$model_name.mar --foreground --log-config /config/log4j2.xml",
    "triton-server":'tritonserver --model-repository=/models/ --strict-model-config=true --log-verbose=1'
}
INFERNENCE_ENV={
    "tfserving":['TF_CPP_VMODULE=http_server=1','TZ=Asia/Shanghai']
}

INFERNENCE_PORTS={
    "tfserving":'8501',
    "torch-server":"8080,8081",
    "triton-server":"8000,8002"
}
INFERNENCE_METRICS={
    "tfserving":'8501:/metrics',
    "torch-server":"8082:/metrics",
    "triton-server":"8002:/metrics"
}
INFERNENCE_HEALTH={
    "tfserving":'8501:/v1/models/$model_name/versions/$model_version/metadata',
    "torch-server":"8080:/ping",
    "triton-server":"8000:/v2/health/ready"
}


sidecars={
    "istio":"流量监控",
    "rate_limit":'限速(企业版)',
    "jwt": 'token认证(企业版)',
    'monitor':'token统计(企业版)',
    'whitelist':'黑白名单(企业版)',
    'quotalimit':'额度限制(企业版)',
    'security':'内容安全(企业版)',
    'search':'联网查询(企业版)',
    "retry":'失败重试(企业版)',
    'desensitization':'数据脱敏(企业版)',
    'prompt':'提示词模板(企业版)',
    'value_map':'参数值映射(企业版)',
    "value_fixed":'参数值固定(企业版)'
}

class InferenceService_Filter(MyappFilter):
    # @pysnooper.snoop()
    def apply(self, query, func):
        if g.user.is_admin():
            return query

        join_projects_id = security_manager.get_join_projects_id(db.session)
        return query.filter(self.model.project_id.in_(join_projects_id))


class InferenceService_ModelView_base():
    datamodel = SQLAInterface(InferenceService)

    # add_columns = ['service_type','project','name', 'label','images','resource_memory','resource_cpu','resource_gpu','min_replicas','max_replicas','ports','host','hpa','metrics','health']
    columns = ['service_type', 'project', 'label', 'model_name', 'model_version', 'images', 'model_path',
                   'resource_memory', 'resource_cpu', 'resource_gpu', 'min_replicas', 'max_replicas', 'hpa', 'priority',
                   'canary', 'shadow', 'host', 'inference_config', 'working_dir', 'command', 'env',
                   'ports', 'metrics', 'health', 'sidecar']
    show_columns = ['service_type', 'project', 'name', 'label', 'model_name', 'model_version', 'images', 'model_path',
                    'images', 'volume_mount', 'sidecar', 'working_dir', 'command', 'env', 'resource_memory',
                    'resource_cpu', 'resource_gpu', 'min_replicas', 'max_replicas', 'ports', 'inference_host_url',
                    'hpa', 'priority', 'canary', 'shadow', 'health', 'model_status', 'expand', 'metrics',
                    'deploy_history', 'host', 'inference_config','changed_on','created_on','id']
    enable_echart = False
    add_columns = columns + ['volume_mount']
    edit_columns = columns + ['volume_mount']

    add_form_query_rel_fields = {
        "project": [["name", Project_Join_Filter, 'org']]
    }
    edit_form_query_rel_fields = add_form_query_rel_fields

    list_columns = ['project', 'service_type', 'label', 'model_name_url', 'model_version', 'inference_host_url', 'ip',
                    'status_url', 'resource', 'replicas_html', 'creator', 'modified', 'operate_html']
    list_select_columns = list_columns+['model_status','changed_on','id']
    cols_width = {
        "project": {"type": "ellip2", "width": 120},
        "label": {"type": "ellip2", "width": 250},
        "service_type": {"type": "ellip2", "width": 150},
        "model_name_url": {"type": "ellip2", "width": 250},
        "model_version": {"type": "ellip2", "width": 150},
        "inference_host_url": {"type": "ellip2", "width": 550},
        "ip": {"type": "ellip2", "width": 200},
        "status_url": {"type": "ellip2", "width": 100},
        "modified": {"type": "ellip2", "width": 150},
        "operate_html": {"type": "ellip2", "width": 170},
        "test": {"type": "ellip1", "width": 50},
        "resource": {"type": "ellip2", "width": 280},
    }
    search_columns = ['name', 'created_by', 'project', 'service_type', 'label', 'model_name', 'model_version',
                      'model_path', 'host', 'model_status', 'resource_gpu']
    ops_link = [
        {
            "text": _("服务资源监控"),
            "url": conf.get('GRAFANA_SERVICE_PATH','/grafana/d/istio-service/istio-service?var-namespace=service&var-service=') + "All"
        }
    ]
    label_title = _('推理服务')
    base_order = ('id', 'desc')
    order_columns = ['id']
    fixed_columns = ['operate_html']

    base_filters = [["id", InferenceService_Filter, lambda: []]]

    service_type_choices = ['serving', 'tfserving', 'torch-server', 'triton-server','ml-server(企业版)',  'vllm(企业版)', 'vllm-distributed(企业版)', 'ollama(企业版)', 'mindie(企业版)', 'mindie-distributed(企业版)']
    spec_label_columns = {
        "inference_host_url": _("域名:需要泛域名支持，调试时域名(debug.xx.xx.xx.xx)")
    }
    service_type_choices = [x.replace('_','-') for x in service_type_choices]
    host_rule=",<br>".join([cluster+"cluster:*."+conf.get('CLUSTERS')[cluster].get("SERVICE_DOMAIN",conf.get('SERVICE_DOMAIN','')) for cluster in conf.get('CLUSTERS') if conf.get('CLUSTERS')[cluster].get("SERVICE_DOMAIN",conf.get('SERVICE_DOMAIN',''))])
    model_path_describe = '''serving：自定义镜像的推理服务，模型地址随意
ml-server：支持sklearn和xgb导出的模型，需按文档设置ml推理服务的配置文件
tfserving：仅支持添加了服务签名的saved_model目录地址，例如：/mnt/xx/../saved_model/
torch-server：torch-model-archiver编译后的mar模型文件，需保存模型结构和模型参数，例如：/mnt/xx/../xx.mar或torch script保存的模型
triton-server：框架:地址。onnx:模型文件地址model.onnx，pytorch:torchscript模型文件地址model.pt，tf:模型目录地址saved_model，tensorrt:模型文件地址model.plan
'''.strip()


    add_form_extra_fields={
        "project": QuerySelectField(
            _('项目组'),
            query_factory=filter_join_org_project,
            allow_blank=True,
            widget=Select2Widget(),
            validators=[DataRequired()]
        ),
        "resource_memory":StringField('memory',default='5G',description= _('内存的资源使用配置，示例1G，10G， 最大100G，如需更多联系管路员'),widget=BS3TextFieldWidget(),validators=[DataRequired(), Regexp("^[0-9]*G$")]),
        "resource_cpu":StringField('cpu', default='5',description= _('cpu的资源使用配置(单位核)，示例 0.4，10，最大50核，如需更多联系管路员'),widget=BS3TextFieldWidget(), validators=[DataRequired(),Regexp("^[0-9]*$")]),
        "min_replicas": StringField(_('最小副本数'), default=InferenceService.min_replicas.default.arg,description= _('最小副本数，用来配置高可用，流量变动自动伸缩'),widget=BS3TextFieldWidget(), validators=[DataRequired(),Regexp("^[0-9]+$")]),
        "max_replicas": StringField(_('最大副本数'), default=InferenceService.max_replicas.default.arg,
                                    description= _('最大副本数，用来配置高可用，流量变动自动伸缩'), widget=BS3TextFieldWidget(),
                                    validators=[DataRequired(),Regexp("^[0-9]+$")]),
        "host": StringField(_('域名'), default=InferenceService.host.default.arg,description= _('访问域名，')+host_rule,widget=BS3TextFieldWidget(),validators=[Regexp('^[\x00-\x7F]*$')]),
        "transformer":StringField(_('前后置处理'), default=InferenceService.transformer.default.arg,description= _('前后置处理逻辑，用于原生开源框架的请求预处理和响应预处理，目前仅支持kfserving下框架'),widget=BS3TextFieldWidget()),
        'resource_gpu':StringField(_('gpu'), default='0', description= _('申请的gpu卡数目，示例:2，每个容器独占整卡。申请具体的卡型号，可以类似 1(V100)，<span style="color:red;">虚拟化占用和共享模式占用仅企业版支持</span>'),
                                                        widget=BS3TextFieldWidget(),validators=[DataRequired(),Regexp('^[\-\.0-9,a-zA-Z\(\)]*$')]),
        "working_dir": StringField(_('工作目录'), description=_('工作目录，容器进程启动目录，不填默认使用Dockerfile内定义的工作目录。')+core.open_jupyter(_('打开目录'),'working_dir'),widget=BS3TextFieldWidget()),

        'sidecar': MySelectMultipleField(
            _('sidecar'),
            default='',
            description = _('容器的agent代理,istio用于服务网格，jwt用于统一认证(需要客户端在请求头中添加开发者生成的token)'),
            widget=Select2ManyWidget(),
            validators=[],
            choices=[[x,sidecars[x]] for x in sidecars]
        ),
        "priority": SelectField(
            _('服务优先级'),
            widget=MySelect2Widget(),
            default=1,
            description= _('优先满足高优先级的资源需求，同时保证每个服务的最低pod副本数'),
            choices=[[1, _('高优先级')], [0, _('低优先级')]],
            validators=[DataRequired()]
        ),
        'model_name': StringField(
            _('模型名称'),
            default='',
            description= _('英文名(小写字母、数字、- 组成)，最长50个字符'),
            widget=MyBS3TextFieldWidget(),
            validators=[DataRequired(), Regexp("^[a-z][a-z0-9\.\/:\-]*[a-z0-9]$"), Length(1, 54)]  #
        ),
        'model_version': StringField(
            _('模型版本号'),
            default=datetime.datetime.now().strftime('v%Y.%m.%d.1'),
            description= _('版本号，时间格式'),
            widget=MyBS3TextFieldWidget(),
            validators=[DataRequired(),Regexp("[a-z0-9_\-\.]*"), Length(1, 54)]
        ),

        'service_type': SelectField(
            _('推理框架类型'),
            default='serving',
            description= _("推理框架类型"),
            widget=MySelect2Widget(retry_info=True),
            choices=[[x, x] for x in service_type_choices],
            validators=[DataRequired()]
        ),
        'label': StringField(
            _('标签'),
            default= _("xx模型，%s框架，xx版"),
            description= _('中文描述'),
            widget=BS3TextFieldWidget(),
            validators=[DataRequired()]
        ),
        "hpa": StringField(
            _('弹性伸缩'),
            default='',
            description= _('弹性伸缩容的触发条件：可以使用cpu/mem/gpu/qps等信息，可以使用其中一个指标或者多个指标，示例：cpu:50%,mem:50%,gpu:50%'),
            widget=BS3TextFieldWidget(),
            validators=[Regexp('^(cpu:|mem:|gpu:|%|,|[0-9])*$')]
        ),
        "cronhpa": StringField(
            _('定时伸缩'),
            default='',
            description=_('根据时间定时伸缩容，定时伸缩时，弹性伸缩容失效。24小时制，示例：9~21:1,21~9:0，表示9点到21点使用一个副本。21点到第二天9点为0个副本'),
            widget=BS3TextFieldWidget(),
            validators=[Regexp('^[0-9~:,]$')]
        ),

        'expand': StringField(
            _('扩展'),
            default=json.dumps({
                "help_url": conf.get('GIT_URL','')+ "/images/serving"
            }, indent=4, ensure_ascii=False),
            description= _('扩展字段，json格式，目前支持help_url帮助文档的地址，disable_load_balancer是否禁用服务的负载均衡'),
            widget=MyBS3TextAreaFieldWidget(rows=3)
        ),

        'canary': StringField(
            _('流量分流'),
            default='',
            description= _('流量分流，将该服务的所有请求，按比例分流到目标服务上。格式 service1:20%,service2:30%，表示分流20%流量到service1，30%到service2'),
            widget=BS3TextFieldWidget(),
            validators=[Regexp('^[0-9a-z:,%]*$')]
        ),

        'shadow': StringField(
            _('流量复制'),
            default='',
            description= _('流量复制，将该服务的所有请求，按比例复制到目标服务上，格式 service1:20%,service2:30%，表示复制20%流量到service1，30%到service2'),
            widget=BS3TextFieldWidget(),
            validators=[Regexp('^[0-9a-z:,%]*$')]
        ),
        'volume_mount': StringField(
            _('挂载'),
            default='',
            description= _('外部挂载，格式:<br>$pvc_name1(pvc):/$container_path1,$hostpath1(hostpath):/$container_path2<br>注意pvc会自动挂载对应目录下的个人username子目录'),
            widget=BS3TextFieldWidget(),
            validators=[Regexp('^[\x00-\x7F]*$')]
        ),
        'model_path': StringField(
            _('模型地址'),
            default='',
            description= _('模型文件的容器地址或下载地址，格式参考详情。')+core.open_jupyter(_('导入模型'),'model_path'),
            widget=MyBS3TextFieldWidget(tips=_(model_path_describe)),
            validators=[]
        ),
        'images': SelectField(
            _('镜像'),
            default='',
            description= _("推理服务镜像"),
            widget=MySelect2Widget(can_input=True),
            choices=[],
            validators=[Regexp('^[\x00-\x7F]*$')]
        ),
        'command': StringField(
            _('启动命令'),
            default='',
            description= _('启动命令，<font color="#FF0000">留空时将被自动重置</font>'),
            widget=MyBS3TextAreaFieldWidget(rows=3)
        ),
        'env': StringField(
            _('环境变量'),
            default='',
            description= _('使用模板的task自动添加的环境变量，支持模板变量。书写格式:每行一个环境变量env_key=env_value'),
            widget=MyBS3TextAreaFieldWidget()
        ),
        'ports': StringField(
            _('端口'),
            default='',
            description= _('监听端口号，逗号分隔'),
            widget=BS3TextFieldWidget(),
            validators=[DataRequired(),Regexp('^[0-9,:]*$')]
        ),
        'metrics': StringField(
            _('指标地址'),
            default='',
            description= _('请求指标采集，配置端口+url，示例：8080:/metrics'),
            widget=BS3TextFieldWidget(),
            validators=[Regexp('^[0-9]+:/[\x00-\x7F]*$')]
        ),
        'health': StringField(
            _('健康检查'),
            default='',
            description= _('健康检查接口，使用http接口，示例：8080:/health'),
            widget=BS3TextFieldWidget(),
            validators=[Regexp('^[0-9]+:/[\x00-\x7F]*$')]
        ),

        'inference_config': StringField(
            _('推理配置文件'),
            default='',
            description= _('会配置文件的形式挂载到容器/config/目录下。<font color="#FF0000">留空时将被自动重置</font>，格式：<br>---文件名<br>多行文件内容<br>---文件名<br>多行文件内容'),
            widget=MyBS3TextAreaFieldWidget(rows=5),
            validators=[]
        )

    }

    input_demo = '''
[
    {
        name: "input_name"
        data_type: TYPE_FP32
        format: FORMAT_NCHW
        dims: [ 3, 224, 224 ]
        reshape: {
            shape: [ 1, 3, 224, 224 ]
        }
    }
]
    '''

    output_demo = '''
[
    {
        name: "output_name"
        data_type: TYPE_FP32
        dims: [ 1000 ]
        reshape: {
            shape: [ 1, 1000 ]
        }
    }
]
    '''

    edit_form_extra_fields = add_form_extra_fields
    # edit_form_extra_fields['name']=StringField(_('名称'), description='英文名(小写字母、数字、- 组成)，最长50个字符',widget=MyBS3TextFieldWidget(readonly=True), validators=[Regexp("^[a-z][a-z0-9\-]*[a-z0-9]$"),Length(1,54)]),

    model_columns = ['service_type', 'project', 'label', 'model_name', 'model_version', 'images', 'model_path']
    service_columns = ['resource_memory', 'resource_cpu', 'resource_gpu', 'min_replicas', 'max_replicas', 'hpa',
                       'priority', 'canary', 'shadow', 'host', 'volume_mount', 'sidecar']
    admin_columns = ['inference_config', 'working_dir', 'command', 'env', 'ports', 'metrics', 'health']

    add_fieldsets = [
        (
            _('模型配置'),
            {"fields": model_columns, "expanded": True},
        ),
        (
            _('推理配置'),
            {"fields": service_columns, "expanded": True},
        ),
        (
            _('管理员配置'),
            {"fields": admin_columns, "expanded": True},
        )
    ]
    add_columns = model_columns + service_columns + admin_columns

    edit_columns = add_columns

    edit_fieldsets = add_fieldsets
    # 检测是否具有编辑权限，只有creator和admin可以编辑
    def check_edit_permission(self, item):
        if g.user and g.user.is_admin():
            return True
        if g.user and g.user.username and hasattr(item, 'created_by'):
            if g.user.username == item.created_by.username:
                return True
        # flash('just creator can edit/delete ', 'warning')
        return False

    check_delete_permission = check_edit_permission

    def pre_add_web(self,item=None):
        self.default_filter = {
            "created_by": g.user.id
        }
        # 修改的时候管理员可以在上面添加一些特殊的挂载配置，适应一些特殊情况
        if not conf.get('ENABLE_USER_VOLUME',False) and not g.user.is_admin():
            self.edit_columns = self.columns
            self.add_columns = self.columns
        else:
            self.add_columns = self.columns + ['volume_mount']
            self.edit_columns = self.columns + ['volume_mount']

    pre_update_web=pre_add_web

    # @pysnooper.snoop()
    def tfserving_model_config(self, model_name, model_version, model_path):
        config_str = '''
model_config_list {
  config {
    name: "%s"
    base_path: "/%s/"
    model_platform: "tensorflow"
    model_version_policy {
        specific {
           versions: %s
        }
    }
  }
}
        ''' % (model_name, model_path.strip('/'), model_version)
        return config_str

    def tfserving_monitoring_config(self):
        config_str = '''
prometheus_config {
  enable: true
  path: "/metrics"
}
        '''
        return config_str

    def tfserving_platform_config(self):
        config_str = '''
platform_configs {
  key: "tensorflow"
  value {
    source_adapter_config {
      [type.googleapis.com/tensorflow.serving.SavedModelBundleSourceAdapterConfig] {
        legacy_config {
          session_config {
            gpu_options {
              allow_growth: true
            }
          }
        }
      }
    }
  }
}
        '''
        return config_str

    # 这些配置可在环境变量中  TS_<PROPERTY_NAME>中实现
    def torch_config(self):
        config_str = '''
inference_address=http://0.0.0.0:8080
management_address=http://0.0.0.0:8081
metrics_address=http://0.0.0.0:8082
cors_allowed_origin=*
cors_allowed_methods=GET, POST, PUT, OPTIONS
cors_allowed_headers=X-Custom-Header
number_of_netty_threads=32
enable_metrics_api=true
job_queue_size=1000
enable_envvars_config=true
async_logging=true
default_response_timeout=120
max_request_size=6553500
vmargs=-Dlog4j.configurationFile=file:///config/log4j2.xml
        '''
        return config_str

    def torch_log(self):
        config_str = '''
<RollingFile name="access_log" fileName="${env:LOG_LOCATION:-logs}/access_log.log" filePattern="${env:LOG_LOCATION:-logs}/access_log.%d{dd-MMM}.log.gz"> 
  <PatternLayout pattern="%d{ISO8601} - %m%n"/>  
  <Policies> 
    <SizeBasedTriggeringPolicy size="100 MB"/>  
    <TimeBasedTriggeringPolicy/> 
  </Policies>  
  <DefaultRolloverStrategy max="5"/> 
</RollingFile>

        '''
        return config_str

    def triton_config(self, item, model_type):
        plat_form = {
            "onnx": "onnxruntime_onnx",
            "tensorrt": "tensorrt_plan",
            "torch": "pytorch_libtorch",
            "pytorch": "pytorch_libtorch",
            "tf": "tensorflow_savedmodel"
        }
        parameters = ''
        if model_type == 'tf':
            parameters = '''
optimization { execution_accelerators { 
    gpu_execution_accelerator : [ { 
        name : "tensorrt"
        parameters { key: "precision_mode" value: "FP16" }}] 
}}
        '''
        if model_type == 'onnx':
            parameters = '''
parameters { key: "intra_op_thread_count" value: { string_value: "0" } }
parameters { key: "execution_mode" value: { string_value: "1" } }
parameters { key: "inter_op_thread_count" value: { string_value: "0" } }
        '''
        if model_type == 'pytorch' or model_type == 'torch':
            parameters = '''
parameters: { key: "DISABLE_OPTIMIZED_EXECUTION" value: { string_value:"true" } }
parameters: { key: "INFERENCE_MODE" value: { string_value: "false" } }

            '''

        config_str = '''
name: "%s"
platform: "%s"
max_batch_size: 0
input %s
output %s
%s
        ''' % (item.model_name, plat_form[model_type], self.input_demo, self.output_demo, parameters)
        return config_str

    # @pysnooper.snoop(watch_explode=('item'))
    def use_expand(self, item):

        # 先存储特定参数到expand
        expand = json.loads(item.expand) if item.expand else {}
        # print(self.src_item_json)
        model_version = item.model_version.replace('v', '').replace('.', '').replace(':', '')
        model_path = "/" + item.model_path.strip('/') if item.model_path else ''

        if not item.ports:
            item.ports = INFERNENCE_PORTS.get(item.service_type,item.ports)
        if not item.env:
            item.env = '\n'.join(INFERNENCE_ENV.get(item.service_type, item.env.split('\n') if item.env else []))
        if not item.metrics:
            item.metrics = INFERNENCE_METRICS.get(item.service_type, item.metrics)
        if not item.health:
            item.health = INFERNENCE_HEALTH.get(item.service_type, '').replace('$model_name',item.model_name).replace('$model_version',item.model_version)
        else:
            item.health = item.health.replace('$model_name',item.model_name).replace('$model_version', item.model_version)

        if not item.host:
            item.host = INFERNENCE_HOST.get(item.service_type, '').replace('$model_name',item.model_name).replace('$model_version',item.model_version)
        else:
            item.host = item.host.replace('$model_name',item.model_name).replace('$model_version', item.model_version)


        # 对网络地址先统一在命令中下载
        download_command = ''
        if 'http:' in item.model_path or 'https:' in item.model_path:
            model_file = item.model_path[item.model_path.rindex('/') + 1:]
            model_path = model_file
            download_command = 'wget %s && ' % item.model_path
            if '.zip' in item.model_path:
                download_command+='unzip -O %s && '%model_file
                model_path = model_file.replace('.zip', '').replace('.tar.gz', '')  # 这就要求压缩文件和目录同名，并且下面直接就是目录。其他格式的文件不能压缩
            if '.tar.gz' in item.model_path:
                download_command += 'tar -zxvf %s && '%model_file
                model_path = model_file.replace('.zip','').replace('.tar.gz','')  # 这就要求压缩文件和目录同名，并且下面直接就是目录。其他格式的文件不能压缩

        if item.service_type == 'tfserving':
            des_model_path = "/models/%s/" % (item.model_name,)
            des_version_path = "/models/%s/%s/" % (item.model_name, model_version)
            if not item.id or not item.command:
                item.command=download_command+'''mkdir -p %s && cp -r %s/* %s  &&  /usr/bin/tf_serving_entrypoint.sh --model_config_file=/config/models.config --monitoring_config_file=/config/monitoring.config --platform_config_file=/config/platform.config'''%(des_version_path,model_path,des_version_path)

            item.health = '8501:/v1/models/%s/versions/%s/metadata' % (item.model_name, model_version)

            expand['models.config']=expand['models.config'] if expand.get('models.config','') else self.tfserving_model_config(item.model_name,model_version,des_model_path)
            expand['monitoring.config']=expand['monitoring.config'] if expand.get('monitoring.config','') else self.tfserving_monitoring_config()
            expand['platform.config'] = expand['platform.config'] if expand.get('platform.config','') else self.tfserving_platform_config()
            if not item.inference_config:
                item.inference_config = '''
---models.config
%s
---monitoring.config
%s
---platform.config
%s
                ''' % (
                    self.tfserving_model_config(item.model_name, model_version, des_model_path),
                    self.tfserving_monitoring_config(),
                    self.tfserving_platform_config()
                )

        if item.service_type == 'ml-server':
            if not item.inference_config:
                item.inference_config = '''
---config.json
[
    {
        "name": "%s",
        "model_path": "%s",
        "framework": "sklearn",
        "version": "%s",
        "enable": true
    }
]

'''%(item.model_name,model_path,item.model_version)
            if not item.command:
                item.command = 'python server.py --config_path /config/config.json'
            if not item.host:
                item.host = f'/v1/models/{item.model_name}/metadata'
            item.health = '80:/v1/models/%s/metadata' % (item.model_name,)

        if item.service_type == 'torch-server':
            if not item.working_dir:
                item.working_dir = '/models'
            model_file = model_path[model_path.rindex('/') + 1:] if '/' in model_path else model_path
            tar_command = 'ls'
            if '.mar' not in model_path:
                tar_command = 'torch-model-archiver --model-name %s --version %s --handler %s --serialized-file %s --export-path /models -f'%(item.model_name,model_version,item.transformer or item.model_type,model_path)
            else:
                if ('http:' in item.model_path or 'https://' in item.model_path) and item.working_dir == '/models':
                    pass
                    # print('has download to des_version_path')
                else:
                    tar_command = 'cp -rf %s /models/' % (model_path)
            if not item.id or not item.command:

                item.command=download_command+'cp /config/* /models/ && '+tar_command+' && torchserve --start --model-store /models --models %s=%s --foreground --ts-config=/config/config.properties'%(item.model_name,model_file)

            expand['config.properties'] = expand['config.properties'] if expand.get('config.properties','') else self.torch_config()
            expand['log4j2.xml'] = expand['log4j2.xml'] if expand.get('log4j2.xml','') else self.torch_log()

            if not item.inference_config:
                item.inference_config = '''
---config.properties
%s
---log4j2.xml
%s
                ''' % (
                    self.torch_config(),
                    self.torch_log()
                )

        if item.service_type == 'triton-server':
            # 识别模型类型
            model_type = 'tf'
            if '.onnx' in model_path:
                model_type = 'onnx'
            if '.plan' in model_path:
                model_type = 'tensorrt'
            if '.pt' in model_path or '.pth' in model_path:
                model_type = 'pytorch'

            if not item.id or not item.command:
                if model_type=='tf':
                    item.command=download_command+'mkdir -p /models/{model_name}/{model_version}/model.savedmodel && cp /config/* /models/{model_name}/ && cp -r /{model_path}/* /models/{model_name}/{model_version}/model.savedmodel && tritonserver --model-repository=/models --strict-model-config=true  --log-verbose=1'.format(model_path=model_path.strip('/'),model_name=item.model_name,model_version=model_version)
                else:
                    model_file_ext = model_path.split(".")[-1]
                    item.command=download_command+'mkdir -p /models/{model_name}/{model_version}/ && cp /config/* /models/{model_name}/ && cp -r {model_path} /models/{model_name}/{model_version}/model.{model_file_ext} && tritonserver --model-repository=/models --strict-model-config=true  --log-verbose=1'.format(model_path=model_path,model_name=item.model_name,model_version=model_version,model_file_ext=model_file_ext)

            config_str = self.triton_config(item, model_type)
            old_config_str = json.loads(self.src_item_json['expand']).get('config.pbtxt', '') if item.id else ''
            new_config_str = expand.get('config.pbtxt', '')
            if not item.id:
                expand['config.pbtxt'] = config_str
            elif new_config_str == old_config_str and new_config_str != config_str:
                expand['config.pbtxt'] = config_str
            elif not new_config_str:
                expand['config.pbtxt'] = config_str

            if not item.inference_config:
                item.inference_config = '''
---config.pbtxt
%s
                    ''' % (
                    config_str,
                )

        # if not item.name:
        item.name = item.model_name.replace('/','-').replace(':','-').replace('.','-').strip('-') + "-" + model_version

        if len(item.name)>60:
            item.name = item.name[:60]
        # item.expand = json.dumps(expand,indent=4,ensure_ascii=False)

    # @pysnooper.snoop()
    def pre_add(self, item):
        if not item.namespace:
            item.namespace = item.project.service_namespace

        if not item.expand:
            item.expand= '{}'
        if item.sidecar:
            item.sidecar = item.sidecar.strip().strip(',')
        if item.name:
            item.name = item.name.replace("_", "-")
        if not item.model_path:
            item.model_path = ''
        if not item.volume_mount:
            item.volume_mount = item.project.volume_mount
        else:
            if conf.get('ENABLE_USER_VOLUME',False) and not g.user.is_admin():
                volume_mounts_temp = re.split(',|;', item.volume_mount)
                volume_mount_arr=[]
                for volume_mount in volume_mounts_temp:
                    match = re.search(r'\((.*?)\)', volume_mount)
                    if match:
                        volume_type = match.group(1)
                        re_str = conf.get('ENABLE_USER_VOLUME_CONFIG', {}).get(volume_type, '')
                        if re_str:
                            if re.match(re_str, volume_mount):
                                volume_mount_arr.append(volume_mount)

                item.volume_mount = ','.join(volume_mount_arr).strip(',')
            # 合并项目组的挂载
            item.volume_mount = core.merge_volume_mount(item.project.volume_mount,item.volume_mount)


        self.use_expand(item)
        item.resource_gpu = item.resource_gpu.upper() if item.resource_gpu else '0'
        if not item.resource_memory:
            item.resource_memory = '2G'
        if not item.resource_cpu:
            item.resource_cpu='2'
        if not item.resource_gpu:
            item.resource_gpu='0'
        # 初始化时没有回话但是也要调用flash，所以会报错
        try:
            if ('http:' in item.model_path or 'https:' in item.model_path) and ('.zip' in item.model_path or '.tar.gz' in item.model_path):
                flash(__('检测到模型地址为网络压缩文件，需压缩文件名和解压后文件夹名相同'), 'warning')
        except Exception as e:
            pass

    def delete_old_service(self, service_name, cluster, namespaces):
        try:
            from myapp.utils.py.py_k8s import K8s
            k8s_client = K8s(cluster.get('KUBECONFIG', ''))
            for namespace in [namespaces, ]:
                for name in [service_name, 'debug-' + service_name, 'test-' + service_name]:
                    service_external_name = (name + "-external").lower()[:60].strip('-')
                    k8s_client.delete_deployment(namespace=namespace, name=name)
                    k8s_client.delete_statefulset(namespace=namespace, name=name)
                    k8s_client.delete_service(namespace=namespace, name=name)
                    k8s_client.delete_service(namespace=namespace, name=service_external_name)
                    k8s_client.delete_istio_ingress(namespace=namespace, name=name)
                    k8s_client.delete_hpa(namespace=namespace, name=name)
                    k8s_client.delete_configmap(namespace=namespace, name=name)
                    k8s_client.delete_crd(group='security.istio.io',version='v1beta1',plural='requestauthentications',namespace=namespace,name=name)
                    k8s_client.delete_crd(group='security.istio.io',version='v1beta1',plural='authorizationpolicies',namespace=namespace,name=name)
        except Exception as e:
            print(e)

    # @pysnooper.snoop(watch_explode=('item',))
    def pre_update(self, item):

        self.pre_add(item)

       
        if self.src_item_json:
            # 如果项目组变了，就删除之前的
            if str(self.src_item_json.get('project_id', '0')) != str(item.project.id):
                from myapp.models.model_team import Project
                old_project = db.session.query(Project).filter_by(id=int(self.src_item_json.get('project_id', '0'))).first()
                if old_project and old_project.cluster['NAME'] != item.project.cluster['NAME']:
                    cluster = conf.get('CLUSTERS').get(old_project.cluster['NAME'])
                    self.delete_old_service(service_name=self.src_item_json.get('name', ''), cluster=cluster, namespaces=item.namespace)
                    flash(__('发现集群更换，启动清理服务'), 'success')

                # 域名后缀如果不一样也要变了
                if old_project and old_project.cluster['SERVICE_DOMAIN'] != item.project.cluster['SERVICE_DOMAIN']:
                    item.host = item.host.replace(old_project.cluster['SERVICE_DOMAIN'], item.project.cluster['SERVICE_DOMAIN'])

            # 如果模型版本和模型名称变了，需要把之前的服务删除掉
            elif self.src_item_json.get('name', '') and item.name != self.src_item_json.get('name', ''):
                self.delete_old_service(service_name=self.src_item_json.get('name', ''), cluster=item.project.cluster, namespaces=item.namespace)
                flash(__("发现模型服务变更，启动清理服务") + '%s:%s' % (self.src_item_json.get('model_name', ''), self.src_item_json.get('model_version', '')), 'success')

        # 如果命名空间变了也要清理掉
        if item.namespace and item.namespace != item.project.service_namespace:
            flash('切换项目组命名空间改变，注意部署前先清理推理服务', 'info')

    # 事后无法读取到project属性
    def pre_delete(self, item):
        self.delete_old_service(service_name=item.name, cluster=item.project.cluster,namespaces=item.namespace)

        flash(__('服务清理完成'), category='success')

    @expose_api(description="清理推理服务",url='/clear/<service_id>', methods=['POST', "GET"])
    def clear(self, service_id):
        service = db.session.query(InferenceService).filter_by(id=service_id).first()
        if service:
            self.delete_old_service(service_name=service.name, cluster=service.project.cluster, namespaces=service.namespace)
            service.model_status = 'offline'
            if not service.deploy_history:
                service.deploy_history=''
            service.deploy_history = service.deploy_history + "\n" + "clear: %s %s" % (g.user.username,datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            db.session.commit()
            flash(__('服务清理完成'), category='success')
        return redirect(conf.get('MODEL_URLS', {}).get('inferenceservice', ''))

    @expose_api(description="部署推理服务调试环境",url='/deploy/debug/<service_id>', methods=['POST', "GET"])
    # @pysnooper.snoop()
    def deploy_debug(self, service_id):
        return self.deploy(service_id, stag='debug')

    @expose_api(description="部署推理服务测试环境",url='/deploy/test/<service_id>', methods=['POST', "GET"])
    # @pysnooper.snoop()
    def deploy_test(self, service_id):
        return self.deploy(service_id, stag='test')

    @expose_api(description="部署推理服务生产环境",url='/deploy/prod/<service_id>', methods=['POST', "GET"])
    # @pysnooper.snoop()
    def deploy_prod(self, service_id):
        return self.deploy(service_id, stag='prod')

    @expose_api(description="推理服务升级",url='/deploy/update/', methods=['POST', 'GET'])
    # @pysnooper.snoop(watch_explode=('deploy'))
    def update_service(self):
        args = request.get_json(silent=True) if request.get_json(silent=True) else {}

        args.update(request.args)
        service_id = int(args.get('service_id', 0))
        service_name = args.get('service_name', '')
        model_name = args.get('model_name', '')
        model_version = args.get('model_version', '')
        service = None

        if service_id:
            service = db.session.query(InferenceService).filter_by(id=service_id).first()
        elif service_name:
            service = db.session.query(InferenceService).filter_by(name=service_name).first()
        elif model_name:
            if model_version:
                service = db.session.query(InferenceService) \
                    .filter(InferenceService.model_name == model_name) \
                    .filter(InferenceService.model_version == model_version) \
                    .filter(InferenceService.model_status == 'online') \
                    .order_by(InferenceService.id.desc()).first()
            else:
                service = db.session.query(InferenceService) \
                    .filter(InferenceService.model_name == model_name) \
                    .filter(InferenceService.model_status == 'online') \
                    .order_by(InferenceService.id.desc()).first()

        if service:
            namespace = service.project.service_namespace
            status = 0
            message = 'success'
            if request.method == 'POST':
                min_replicas = int(args.get('min_replicas', 0))
                if min_replicas:
                    service.min_replicas = min_replicas
                    if service.max_replicas < min_replicas:
                        service.max_replicas = min_replicas
                    db.session.commit()
                    try:
                        self.deploy(service.id)
                    except Exception as e:
                        print(e)
                        status = -1
                        message = str(e)
                time.sleep(3)

            from myapp.utils.py.py_k8s import K8s
            k8s_client = K8s(service.project.cluster.get('KUBECONFIG', ''))
            deploy = None
            try:
                deploy = k8s_client.AppsV1Api.read_namespaced_deployment(name=service.name, namespace=namespace)
            except Exception as e:
                print(e)
                status = -1,
                message = str(e)

            back = {
                "result": {
                    "service": service.to_json(),
                    "deploy": deploy.to_dict() if deploy else {}
                },
                "status": status,
                "message": message
            }

            return jsonify(back)

        else:
            return jsonify({
                "result": "",
                "status": -1,
                "message": "service not exist or service not online"
            })

    # @pysnooper.snoop()
    def deploy(self, service_id, stag='prod'):
        service = db.session.query(InferenceService).filter_by(id=service_id).first()
        if service.model_status != 'offline' and service.model_status != 'debug' and 'distributed' in service.service_type:
            flash(f'分布式推理部署前需前清理服务', category='warning')
            return redirect(conf.get('MODEL_URLS', {}).get('inferenceservice','/frontend/service/inferenceservice/inferenceservice_manager'))

        if service.model_status!='offline' and service.model_status!=stag:
            if stag=='prod' and service.model_status=='online':
                pass
            else:
                flash(f'检测到推理服务状态{service.model_status}，请先清理再部署',category='warning')
                return redirect(conf.get('MODEL_URLS',{}).get('inferenceservice','/frontend/service/inferenceservice/inferenceservice_manager'))


        namespace = service.project.service_namespace

        name = service.name
        command = service.command
        command = command.replace('$model_path', service.model_path).replace('$model_name', service.model_name).replace("{{creator}}", service.created_by.username)
        deployment_replicas = service.min_replicas
        if stag == 'debug':
            name = stag + '-' + service.name
            command = 'sleep 43200'
            deployment_replicas = 1

        if stag == 'test':
            name = stag + '-' + service.name
            # namespace=pre_namespace


        image_pull_secrets = conf.get('HUBSECRET', [])
        user_repositorys = db.session.query(Repository).filter(Repository.created_by_fk == g.user.id).all()
        image_pull_secrets = list(set(image_pull_secrets + [rep.hubsecret for rep in user_repositorys]))

        from myapp.utils.py.py_k8s import K8s
        k8s_client = K8s(service.project.cluster.get('KUBECONFIG', ''))

        config_datas = service.inference_config.strip().split("\n---") if service.inference_config else []
        config_datas = [x.strip() for x in config_datas if x.strip()]
        volume_mount = service.volume_mount
        # print('文件个数：', len(config_datas))
        config_data = {}
        for data in config_datas:
            file_name = re.sub('^-*', '', data.split('\n')[0]).strip()
            file_content = '\n'.join(data.split('\n')[1:])
            if file_name and file_content:
                config_data[file_name] = file_content
        if config_data:
            # print('create configmap')
            k8s_client.create_configmap(namespace=namespace, name=name, data=config_data, labels={'app': name})
            volume_mount += ",%s(configmap):/config/" % name

        # 对挂载做一下渲染替换，可以替换用户名，也可以替换环境变量
        volume_mount = volume_mount.replace("{{creator}}", service.created_by.username)
        if service.env:
            for e in service.env.split("\n"):
                if '=' in e:
                    volume_mount = volume_mount.replace('{{' + e.split("=")[0] + '}}', e.split("=")[1])

        ports = [int(port) for port in service.ports.replace('，',',').split(',')]
        gpu_num, _, _ = core.get_gpu(service.resource_gpu)

        pod_env = service.env.strip()
        pod_env += "\nKUBEFLOW_ENV=" + stag
        pod_env += '\nKUBEFLOW_MODEL_PATH=' + (service.model_path if service.model_path else '')
        pod_env += '\nKUBEFLOW_MODEL_VERSION=' + service.model_version
        pod_env += '\nKUBEFLOW_MODEL_IMAGES=' + service.images
        pod_env += '\nKUBEFLOW_MODEL_NAME=' + service.model_name
        pod_env += '\nKUBEFLOW_INFERENCE_ID=' + str(service.id)
        pod_env += '\nKUBEFLOW_RUN_ID=' + str(uuid.uuid4().hex[:4])
        pod_env += "\nRESOURCE_CPU=" + service.resource_cpu
        pod_env += "\nRESOURCE_MEMORY=" + service.resource_memory
        pod_env += "\nRESOURCE_MIN_REPLICAS=" + str(service.min_replicas)
        pod_env += "\nRESOURCE_MAX_REPLICAS=" + str(service.max_replicas)
        pod_env += "\nRESOURCE_GPU=" + str(gpu_num).replace('，',',').split(',')[-1]
        pod_env += "\nMODEL_PATH=" + service.model_path.rstrip('/')
        pod_env += "\nMODEL_NAME=" + service.model_name
        pod_env += "\nINFERENCE_NAME=" + name
        # pod_env += "\nSECRET=" + service.created_by.secret

        pod_env = pod_env.strip(',')
        pod_env = pod_env.replace('$model_path',service.model_path).replace('$model_name',service.model_name).replace("{{creator}}", service.created_by.username)


        sidecar_contaners = []

        if stag == 'test' or stag == 'debug':
            try:
                # print('delete deployment')
                k8s_client.delete_deployment(namespace=service.namespace, name=name)
                k8s_client.delete_statefulset(namespace=service.namespace, name=name)
            except Exception as e:
                print(e)
        # 因为所有的服务流量通过ingress实现，所以没有isito的envoy代理
        labels = {"app": name,  "user": service.created_by.username, 'pod-type': "inference"}

        try:
            pod_ports = copy.deepcopy(ports)
            try:
                if service.metrics and service.metrics.strip():
                    metrics_port = int(service.metrics[:service.metrics.index(":")])
                    pod_ports.append(metrics_port)
            except Exception as e:
                print(e)

            try:
                if service.health and service.health.strip():
                    health_port = int(service.health[:service.health.index(":")])
                    pod_ports.append(health_port)
            except Exception as e:
                pass
                # print(e)

            pod_ports = list(set(pod_ports))
            # print('create deployment')
            # https://istio.io/latest/docs/reference/config/annotations/
            if service.sidecar and 'istio' in service.sidecar:  #  and service.service_type == 'serving'
                labels['sidecar.istio.io/inject'] = 'true'

            pod_annotations = {
                'project': service.project.name
            }
            service.namespace=namespace
            db.session.commit()
            service.namespace=namespace
            db.session.commit()
            k8s_client.create_deployment(
                namespace=namespace,
                name=name,
                replicas=deployment_replicas,
                labels=labels,
                annotations=pod_annotations,
                command=['bash', '-c', command] if command else None,
                args=None,
                volume_mount=volume_mount,
                working_dir=service.working_dir.replace('{{creator}}',service.created_by.username),
                node_selector=service.get_node_selector(),
                resource_memory=service.resource_memory,
                resource_cpu=service.resource_cpu,
                resource_gpu=service.resource_gpu if service.resource_gpu else '',
                image_pull_policy=conf.get('IMAGE_PULL_POLICY', 'Always'),
                image_pull_secrets=image_pull_secrets,
                image=service.images,
                hostAliases=conf.get('HOSTALIASES', ''),
                env=pod_env,
                privileged=False,
                accounts=None,
                username=service.created_by.username,
                ports=pod_ports,
                health=service.health if ':' in service.health and stag != 'debug' else None
            )
        except Exception as e:
            flash('deploymnet:' + str(e), 'warning')

        # 监控
        if service.metrics:
            annotations = {
                "prometheus.io/scrape": "true",
                "prometheus.io/port": service.metrics.split(":")[0],
                "prometheus.io/path": service.metrics.split(":")[1]
            }
        else:
            annotations = {}
        # print('deploy service')
        # 端口改变才重新部署服务
        disable_load_balancer = str(json.loads(service.expand).get('disable_load_balancer','false')).lower() if service.expand else 'false'
        if disable_load_balancer=='true':
            disable_load_balancer=True
        else:
            disable_load_balancer=False

        k8s_client.create_service(
            namespace=namespace,
            name=name,
            username=service.created_by.username,
            ports=ports,
            annotations=annotations,
            selector=labels,
            disable_load_balancer=disable_load_balancer
        )

        # 如果域名配置的gateway，就用这个
        host = service.name + "." + service.project.cluster.get('SERVICE_DOMAIN', conf.get('SERVICE_DOMAIN', ''))

        # 如果系统配置了host，并且不是ip
        if service.host and not core.checkip(service.host):
            config_host = service.host.replace('http://', '').replace('https://', '').strip()
            if "/" in config_host:
                config_host = config_host[:config_host.index("/")]
            if config_host:
                host=config_host
        # 前缀来区分不同的环境服务
        if host and (stag == 'debug' or stag == 'test'):
            host = stag + '.' + host
        try:
            if not core.checkip(host):
                # print('deploy istio ingressgateway')
                k8s_client.create_istio_ingress(
                    namespace=namespace,
                    name=name,
                    host=host,
                    ports=service.ports.replace('，',',').split(','),
                    canary=service.canary,
                    shadow=service.shadow
                )
        except Exception as e:
            print(e)

        # 以ip形式访问的话，使用的代理ip。不然不好处理机器服务化机器扩容和缩容时ip变化

        SERVICE_EXTERNAL_IP = []
        # 使用项目组ip
        if service.project.expand:
            ip = json.loads(service.project.expand).get('SERVICE_EXTERNAL_IP', '')
            if ip and type(ip) == str:
                SERVICE_EXTERNAL_IP = [ip]
            if ip and type(ip) == list:
                SERVICE_EXTERNAL_IP = ip

        # 使用集群的ip
        if not SERVICE_EXTERNAL_IP:
            ip = service.project.cluster.get('HOST','').split('|')[0].strip().split(':')[0]
            if ip:
                SERVICE_EXTERNAL_IP=[ip]

        # 使用全局ip
        if not SERVICE_EXTERNAL_IP:
            SERVICE_EXTERNAL_IP = conf.get('SERVICE_EXTERNAL_IP', None)

        # 使用当前ip
        if not SERVICE_EXTERNAL_IP:
            ip = request.host.split(':')[0]
            if '127.0.0.1' in ip:
                host = service.project.cluster.get('HOST', '').split('|')[0].strip().split(':')[0]
                if host:
                    SERVICE_EXTERNAL_IP = [host]

            elif core.checkip(ip):
                SERVICE_EXTERNAL_IP = [ip]

        if SERVICE_EXTERNAL_IP:
            # 对于多网卡模式，或者单域名模式，代理需要配置内网ip，界面访问需要公网ip或域名
            SERVICE_EXTERNAL_IP = [ip.split('|')[0].strip().split(':')[0] for ip in SERVICE_EXTERNAL_IP]
            port_str = conf.get('INFERENCE_PORT', '20000+10*ID').replace('ID', str(service.id))
            meet_ports = core.get_not_black_port(int(eval(port_str)))
            service_ports = [[meet_ports[index], port] for index, port in enumerate(ports)]
            service_external_name = (service.name + "-external").lower()[:60].strip('-')
            # print('deploy proxy ip')
            # 监控
            annotations = {
                "service.kubernetes.io/local-svc-only-bind-node-with-pod": "true",
                "service.cloud.tencent.com/local-svc-weighted-balance": "true"
            }
            if meet_ports[0]<30000:
                k8s_client.create_service(
                    namespace=namespace,
                    name=service_external_name,
                    username=service.created_by.username,
                    annotations=annotations,
                    ports=service_ports,
                    selector=labels,
                    service_type='ClusterIP' if conf.get('K8S_NETWORK_MODE', 'iptables') != 'ipvs' else 'NodePort',
                    external_ip=SERVICE_EXTERNAL_IP if conf.get('K8S_NETWORK_MODE', 'iptables') != 'ipvs' else None
                    # external_traffic_policy='Local'
                )
            else:
                flash(__('端口已耗尽，后续请使用泛域名访问服务'), 'warning')
        # # 以ip形式访问的话，使用的代理ip。不然不好处理机器服务化机器扩容和缩容时ip变化
        # ip和端口形式只定向到生产，因为不能像泛化域名一样随意添加
        TKE_EXISTED_LBID = ''
        if service.project.expand:
            TKE_EXISTED_LBID = json.loads(service.project.expand).get('TKE_EXISTED_LBID', "")
        if not TKE_EXISTED_LBID:
            TKE_EXISTED_LBID = service.project.cluster.get("TKE_EXISTED_LBID", '')
        if not TKE_EXISTED_LBID:
            TKE_EXISTED_LBID = conf.get('TKE_EXISTED_LBID', '')

        if not SERVICE_EXTERNAL_IP and TKE_EXISTED_LBID:
            TKE_EXISTED_LBID = TKE_EXISTED_LBID.split('|')[0].strip().split(':')[0]
            port_str = conf.get('INFERENCE_PORT', '20000+10*ID').replace('ID', str(service.id))
            meet_ports = core.get_not_black_port(int(eval(port_str)))
            service_ports = [[meet_ports[index], port] for index, port in enumerate(ports)]
            service_external_name = (service.name + "-external").lower()[:60].strip('-')
            if meet_ports[0] < 30000:
                k8s_client.create_service(
                    namespace=namespace,
                    name=service_external_name,
                    username=service.created_by.username,
                    ports=service_ports,
                    selector=labels,
                    service_type='LoadBalancer',
                    annotations={
                        "service.kubernetes.io/tke-existed-lbid": TKE_EXISTED_LBID,
                    }
                )
            else:
                flash(__('端口已耗尽，后续请使用泛域名访问服务'), 'warning')

        if stag == 'prod':
            hpas = re.split(',|;', service.hpa)
            regex = re.compile(r"\(.*\)")
            if float(regex.sub('', service.resource_gpu)) < 1:
                for hpa in copy.deepcopy(hpas):
                    if 'gpu' in hpa:
                        hpas.remove(hpa)

            # 伸缩容
            if int(service.max_replicas) > int(service.min_replicas) and service.hpa:
                try:
                    # 创建+绑定deployment
                    # print('create hpa')
                    k8s_client.create_hpa(
                        namespace=namespace,
                        name=name,
                        min_replicas=int(service.min_replicas),
                        max_replicas=int(service.max_replicas),
                        hpa=','.join(hpas)
                    )
                except Exception as e:
                    flash('hpa:' + str(e), 'warning')
            else:
                k8s_client.delete_hpa(namespace=namespace, name=name)

        # # 使用激活器
        # if int(service.min_replicas)==0:
        #     flash('检测到最小副本为0，已加入激活器装置')
        #     pass

        # 不记录部署测试的情况
        if stag == 'debug' and service.model_status == 'offline':
            service.model_status = 'debug'
        if stag == 'test' and service.model_status == 'offline':
            service.model_status = 'test'

        if stag == 'prod':
            service.model_status = 'online'
        service.deploy_history=service.deploy_history+"\n"+"deploy %s: %s %s"%(stag,g.user.username,datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        service.deploy_history = '\n'.join(service.deploy_history.split("\n")[-10:])
        db.session.commit()
        if stag == "debug":
            time.sleep(2)
            # 可能是之前debug了，现在可以直接打开
            pods = k8s_client.get_pods(namespace=namespace, labels={"app": name})
            if pods:
                pod = pods[0]
                # print('deploy debug success')
                return redirect("/k8s/web/debug/%s/%s/%s/%s" % (service.project.cluster['NAME'], namespace, pod['name'],name))

        # 生产环境才有域名代理灰度的问题
        if stag == 'prod':
            from myapp.tasks.async_task import upgrade_service
            kwargs = {
                "service_id": service.id,
                "name": service.name,
                "namespace": namespace
            }
            upgrade_service.apply_async(kwargs=kwargs)

        flash(__('服务部署完成，正在进行同域名服务版本切换'), category='success')
        # print('deploy prod success')
        return redirect(conf.get('MODEL_URLS', {}).get('inferenceservice', ''))

    @action("copy", "复制", confirmation= '复制所选记录?', icon="fa-copy", multiple=True, single=False)
    def copy(self, services):
        if not isinstance(services, list):
            services = [services]
        try:
            for service in services:
                new_services = service.clone()
                index = 1
                model_version = datetime.datetime.now().strftime('v%Y.%m.%d.1')
                while True:
                    model_version = datetime.datetime.now().strftime('v%Y.%m.%d.'+str(index))
                    exits_service = db.session.query(InferenceService).filter_by(model_version=model_version).filter_by(model_name=new_services.model_name).first()
                    if exits_service:
                        index += 1
                    else:
                        break

                new_services.model_version=model_version
                new_services.name = (new_services.model_name.replace('/','-').replace(':','-').replace('.','-').strip('-')+"-"+new_services.model_version.replace('v','').replace('.',''))[:60]
                new_services.created_on = datetime.datetime.now()
                new_services.changed_on = datetime.datetime.now()
                db.session.add(new_services)
                db.session.commit()
        except InvalidRequestError:
            db.session.rollback()
        except Exception as e:
            raise e
        return redirect(request.referrer)

    # 划分数据历史版本
    # @pysnooper.snoop()
    def pre_list_res(self,res):
        data=res['data']
        import itertools
        all_data={item['id']:item for item in data}
        all_last_data_id=[]
        # 按name分组，最新数据下包含其他更老的数据作为历史集合
        data = sorted(data, key=lambda x: re.search(r'>(.*?)</a>',x['model_name_url']).group(1))
        for name, group in itertools.groupby(data, key=lambda x: re.search(r'>(.*?)</a>',x['model_name_url']).group(1)):
            group=list(group)
            # 优先显示在线的服务。
            online_id = [x['id'] for x in group if x.get("model_status","offline")=='online']
            # # 按修改时间进行排序，这个需要list接口中返回changed_on
            if not online_id:
                exist_services = sorted(group,key=lambda x:x['changed_on'],reverse=True)
                online_id = [x['id'] for x in exist_services]
            # max_id = online_id
            max_id = max([x['id'] for x in group]) if not online_id else online_id[0]
            all_last_data_id.append(max_id)
            for item in group:
                if item['id']!=max_id:
                    if 'children' not in all_data[max_id]:
                        all_data[max_id]['children']=[all_data[item['id']]]
                    else:
                        all_data[max_id]['children'].append(all_data[item['id']])
        # 顶层只保留最新的数据
        res['data'] = [all_data[id] for id in all_data if id in all_last_data_id]
        return res


# 添加api
class InferenceService_ModelView_Api(InferenceService_ModelView_base, MyappModelRestApi):
    datamodel = SQLAInterface(InferenceService)
    route_base = '/inferenceservice_modelview/api'

    # 目前 编辑时的列，是使用第一次打开时info接口拿到的edit_column而不是 点击编辑时拿到的info信息
    # @pysnooper.snoop()
    def set_columns_related(self, exist_add_args, response_add_columns):
        exist_service_type = exist_add_args.get('service_type', '')

        response_add_columns['images']['values'] = [{"id":x,"value":x} for x in conf.get('INFERNENCE_IMAGES',{}).get(exist_service_type,[])]
        response_add_columns['images']['default'] = ''
        response_add_columns['model_path']['default']=INFERNENCE_MODEL_PATH.get(exist_service_type,'')
        response_add_columns['command']['default'] = INFERNENCE_COMMAND.get(exist_service_type,'')
        response_add_columns['inference_config']['default'] = INFERNENCE_CONFIGMAP.get(exist_service_type, '')
        response_add_columns['host']['default'] = INFERNENCE_HOST.get(exist_service_type, '')
        response_add_columns['env']['default'] = '\n'.join(INFERNENCE_ENV.get(exist_service_type,[]))
        response_add_columns['ports']['default'] = INFERNENCE_PORTS.get(exist_service_type,'80')
        response_add_columns['metrics']['default'] = INFERNENCE_METRICS.get(exist_service_type,'')
        response_add_columns['health']['default'] = INFERNENCE_HEALTH.get(exist_service_type,'')

        # if exist_service_type!='triton-server' and "inference_config" in response_add_columns:
        #     del response_add_columns['inference_config']


appbuilder.add_api(InferenceService_ModelView_Api)
