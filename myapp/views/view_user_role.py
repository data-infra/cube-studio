import re

import pysnooper
from flask import jsonify,request
from myapp.views.baseSQLA import MyappSQLAInterface as SQLAInterface
from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
from wtforms import SelectField, StringField
from myapp import appbuilder, conf
from flask_appbuilder.fieldwidgets import Select2Widget, BS3TextFieldWidget, Select2ManyWidget
from flask_appbuilder.baseviews import expose_api
from wtforms.validators import DataRequired, Regexp
from werkzeug.security import generate_password_hash,check_password_hash
from flask import (
    flash,
    g
)
from .baseApi import (
    MyappModelRestApi
)
import json
from myapp.security import MyUser, MyRole, MyUserRemoteUserModelView_Base
from myapp import db,cache



class User_ModelView_Base(MyUserRemoteUserModelView_Base):

    list_columns = ["username",'nickname', "active", "roles_html", 'org']
    cols_width = {
        "username": {"type": "ellip1", "width": 150},
        "nickname": {"type": "ellip1", "width": 100},
        "active": {"type": "ellip1", "width": 100},
        "roles_html": {"type": "ellip1", "width": 200},
        "org": {"type": "ellip2", "width": 400}
    }
    spec_label_columns = {
        "get_full_name": _("全名称"),
        "first_name": _("姓"),
        "last_name": _("名"),
        "username": _("用户名"),
        "password": _("密码"),
        "active": _("激活"),
        "email": _("邮箱"),
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

# 添加api
class User_ModelView_Api(User_ModelView_Base, MyappModelRestApi):
    datamodel = SQLAInterface(MyUser)
    route_base = '/users/api'


appbuilder.add_api(User_ModelView_Api)


# 添加api
class UserInfo_ModelView_Api(User_ModelView_Base, MyappModelRestApi):
    datamodel = SQLAInterface(MyUser)
    route_base = '/userinfo/api'
    label_title = _('用户信息')
    base_permissions = []

    edit_columns = ['nickname','password', "email", 'org']
    show_columns = ["username",'nickname','email','org','quota', "roles",'secret']

    # 打开标注平台获取的用户项目组
    @expose_api(description="个人信息",url="/current/userinfo", methods=["GET","POST"])
    def current_userinfo(self):
        if request.method == "GET":
            return jsonify({
                "username": g.user.username,
                "email": g.user.email,
                "nickname": g.user.nickname,
                "roles": ','.join([role.name for role in g.user.roles]),
                "active": g.user.active,
                "org": g.user.org,
                "quota": g.user.quota,
                "secret": g.user.secret,
                "balance": g.user.balance,
                "created_on": g.user.created_on,
                "changed_on": g.user.changed_on,
                "wechat": g.user.wechat
            })
        elif request.method == "POST":
            json_data = request.get_json(silent=True)
            user = db.session.query(MyUser).filter_by(id=g.user.id).first()
            user1 = db.session.query(MyUser).filter_by(username=user.username).first()
            user2 = db.session.query(MyUser).filter_by(email=user.email).first()
            if user1 and user1.id!=user.id or user2 and user2.id!=user.id:
                flash(_("用户名或邮箱已存在"))
                return self.response(400,**{"status": 1, "message": '用户名或邮箱已存在', "result": {}})
            user.username = json_data.get("username",user.username)
            new_password = json_data.get("password",user.password)
            user.password = new_password if new_password else user.password
            if new_password and 'pbkdf2:sha256:' not in new_password:
                user.password = generate_password_hash(new_password)

            user.org = json_data.get("org", user.org)
            user.email = json_data.get("email", user.email)
            user.nickname = json_data.get("nickname", user.nickname)
            user.wechat = json_data.get("wechat", user.wechat)
            db.session.commit()
            return self.response(200,**{"status": 0, "message": '修正完成', "result": {}})

appbuilder.add_api(UserInfo_ModelView_Api)


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
