import re

from myapp.views.baseSQLA import MyappSQLAInterface as SQLAInterface
from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
from wtforms import SelectField, StringField
from myapp import appbuilder, conf
from flask_appbuilder.fieldwidgets import Select2Widget, BS3TextFieldWidget, Select2ManyWidget

from wtforms.validators import DataRequired, Regexp
from flask import (
    flash,
    g
)
from .baseApi import (
    MyappModelRestApi
)
import json
from flask_appbuilder import CompactCRUDMixin, expose
from myapp.security import MyUser, MyRole


class User_ModelView_Base():
    label_title = _('用户')
    datamodel = SQLAInterface(MyUser)

    base_permissions = ['can_list', 'can_edit', 'can_add', 'can_show','can_userinfo']

    list_columns = ["username", "active", "roles_html"]

    edit_columns = ["username",'password', "active", "email", 'org', 'quota', 'roles']
    add_columns = ["username",'password', "email", 'org', 'quota', 'roles']
    show_columns = ["username", "active",'email','org','quota','password', "roles_html",'secret','roles']
    describe_columns={
        "org":"组织架构，自行填写",
        "quota": '资源限额，额度填写方式 $集群名,$资源组名,$命名空间,$资源类型,$限制类型,$限制值，其中$命名空间包含all,jupyter,pipeline,service,automl,aihub,$资源类型包含cpu,memory,gpu,$限制类型包含single,concurrent,total',
        "roles": "Admin角色拥有管理员权限，Gamma为普通用户角色"
    }
    spec_label_columns = {
        "get_full_name": _("全名称"),
        "first_name": _("姓"),
        "last_name": _("名"),
        "username": _("用户名"),
        "password": _("密码"),
        "active": _("激活"),
        "email": _("邮件"),
        "roles": _("角色"),
        "roles_html": _("角色"),
        "last_login": _("最近一次登录"),
        "login_count": _("登录次数"),
        "fail_login_count": _("登录失败次数"),
        "created_on": _("创建时间"),
        "created_by": _("创建者"),
        "changed_on": _("修改时间"),
        "changed_by": _("修改者"),
        "secret": _("秘钥"),
        "quota": _('额度'),
        "org": _("组织架构")
    }

    order_columns=['id']
    search_columns = ["username", 'org']
    base_order = ('id', 'desc')
    # 个人查看详情额展示的信息
    user_show_fieldsets = [
        (
            _("User info"),
            {"fields": ["username", "active", "roles", "email",'secret','org','quota']},
        )
    ]
    show_fieldsets = user_show_fieldsets

    add_form_extra_fields = {
        "username" : StringField(
            _("用户名"),
            validators=[DataRequired(), Regexp("^[a-z][a-z0-9\-]*[a-z0-9]$")],
            widget=BS3TextFieldWidget(),
            description=_("用户名只能由小写字母、数字、-组成"),
        ),
        "password": StringField(
            _("密码"),
            validators=[DataRequired()],
            widget=BS3TextFieldWidget()
        ),
        "email":StringField(
            _("邮箱"),
            validators=[DataRequired(), Regexp(".*@.*.com")],
            widget=BS3TextFieldWidget()
        ),
        "org": StringField(
            _("组织架构"),
            widget=BS3TextFieldWidget(),
            description=_("组织架构，自行填写"),
        ),
        "quota": StringField(
            _("额度限制"),
            widget=BS3TextFieldWidget(),
            description=_('用户在该项目组中的资源额度,<br>额度填写方式 $命名空间,$资源类型,$限制类型,$限制值，<br>其中$命名空间包含all,jupyter,pipeline,service,automl,aihub,<br>$资源类型包含cpu,memory,gpu,<br>$限制类型包含single,concurrent,total，<br>多个限额配置使用分隔分隔')
        )
    }
    edit_form_extra_fields = add_form_extra_fields

    @expose("/userinfo/")
    # @has_access
    def userinfo(self):
        item = self.datamodel.get(g.user.id, self._base_filters)
        widgets = self._get_show_widget(
            g.user.id, item, show_fieldsets=self.user_show_fieldsets
        )
        self.update_redirect()
        return self.render_template(
            self.show_template,
            title=self.user_info_title,
            widgets=widgets,
            appbuilder=self.appbuilder,
        )

    # 添加默认gamma角色
    # @pysnooper.snoop()
    def post_add(self,user):
        from myapp import security_manager,db
        gamma_role = security_manager.find_role('Gamma')
        if gamma_role not in user.roles and not user.roles:
            user.roles.append(gamma_role)
            db.session.commit()

        # 添加到public项目组
        try:
            from myapp.models.model_team import Project_User, Project
            public_project = db.session.query(Project).filter(Project.name == "public").filter(Project.type == "org").first()
            if public_project:
                project_user = Project_User()
                project_user.project = public_project
                project_user.role = 'dev'
                project_user.user_id = user.id
                db.session.add(project_user)
                db.session.commit()
        except Exception:
            db.session.rollback()

        # 在标注平台中添加用户
        try:
            from myapp.utils.labelstudio import LabelStudio
            labelstudio = LabelStudio()
            labelstudio.add_user(user=user,username=user.username)   # 这里username应该用修改前的username，好知道修改labelstudio里面的哪个用户名
        except Exception as labelstudio_e:
            print(labelstudio_e)

    def post_update(self,user):
        # 如果修改了账户，要更改labelstudio中的账户
        self.post_add(user)

    def pre_add(self,user):
        user.first_name = user.username
        user.last_name = ''

# 添加api
class User_ModelView_Api(User_ModelView_Base, MyappModelRestApi):
    datamodel = SQLAInterface(MyUser)
    route_base = '/users/api'

appbuilder.add_api(User_ModelView_Api)




class Role_ModelView_Base():
    label_title = _('角色')
    datamodel = SQLAInterface(MyRole)

    base_permissions = ['can_list', 'can_show', 'can_add', 'can_edit']
    edit_columns = ["name", 'permissions']
    add_columns = edit_columns
    show_columns = ["name", "permissions"]
    list_columns = ["name", "permissions_html"]
    spec_label_columns = {
        "name":_("名称"),
        "permissions":_("权限"),
        "permissions_html": _("权限"),
        "user":_("用户"),
        "user_html": _("用户"),
    }
    cols_width = {
        "name": {"type": "ellip2", "width": 100},
        "permissions_html": {"type": "ellip2", "width": 700}
    }

    order_columns=['id']
    search_columns = ["name"]
    base_order = ('id', 'desc')

# 添加api
class Role_ModelView_Api(Role_ModelView_Base, MyappModelRestApi):
    datamodel = SQLAInterface(MyRole)
    route_base = '/roles/api'

appbuilder.add_api(Role_ModelView_Api)
