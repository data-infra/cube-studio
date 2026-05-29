import datetime
import functools
import logging
import traceback
import pysnooper
from typing import Any, Dict
from flask_appbuilder.forms import GeneralModelConverter
from flask import get_flashed_messages
from flask_appbuilder.actions import action
from flask_appbuilder.forms import DynamicForm
from flask_appbuilder.models.sqla.filters import BaseFilter
from myapp.forms import MySearchWidget
from flask_babel import get_locale
from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
from flask_wtf.form import FlaskForm
import simplejson as json
from werkzeug.exceptions import HTTPException
from wtforms.fields.core import Field, UnboundField
from flask_appbuilder import ModelView
from flask_appbuilder.baseviews import BaseCRUDView, BaseView, expose
from myapp import conf, db, get_feature_flags, security_manager, event_logger
from myapp.exceptions import MyappException, MyappSecurityException
from myapp.utils import core
from flask_appbuilder.urltools import (
    get_filter_args,
    get_order_args,
    get_page_args,
    get_page_size_args,
)
from flask import (
    g,
    redirect as flask_redirect,
    request,
    Response,
)


import yaml

FRONTEND_CONF_KEYS = (
    "MYAPP_WEBSERVER_TIMEOUT",
    "ENABLE_JAVASCRIPT_CONTROLS",
    "MYAPP_WEBSERVER_DOMAINS",
)



def get_error_msg():
    if conf.get("SHOW_STACKTRACE"):
        error_msg = traceback.format_exc()
    else:
        error_msg = "FATAL ERROR \n"
        error_msg += (
            "Stacktrace is hidden. Change the SHOW_STACKTRACE "
            "configuration setting to enable it"
        )
    return error_msg


def json_error_response(msg=None, status=500, stacktrace=None, payload=None, link=None):
    if not payload:
        payload = {"error": "{}".format(msg)}
        payload["stacktrace"] = core.get_stacktrace()
    if link:
        payload["link"] = link

    return Response(
        json.dumps(payload, default=core.json_iso_dttm_ser, ignore_nan=True),
        status=status,
        mimetype="application/json",
    )


def json_response(message, status, result):
    return jsonify(
        {
            "message": message,
            "status": status,
            "result": result
        }
    )


def json_success(json_msg, status=200):
    return Response(json_msg, status=status, mimetype="application/json")


def data_payload_response(payload_json, has_error=False):
    status = 400 if has_error else 200
    return json_success(payload_json, status=status)


# 产生下载csv的响应header
def generate_download_headers(extension, filename=None):
    filename = filename if filename else datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    content_disp = "attachment; filename={}.{}".format(filename, extension)
    headers = {"Content-Disposition": content_disp}
    return headers


def api(f):
    """
    A decorator to label an endpoint as an API. Catches uncaught exceptions and
    return the response in the JSON format
    """

    def wraps(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except Exception as e:
            logging.exception(e)
            return json_error_response(get_error_msg())

    return functools.update_wrapper(wraps, f)


def handle_api_exception(f):
    """
    A decorator to catch myapp exceptions. Use it after the @api decorator above
    so myapp exception handler is triggered before the handler for generic
    exceptions.
    """

    def wraps(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except MyappSecurityException as e:
            logging.exception(e)
            return json_error_response(
                core.error_msg_from_exception(e),
                status=e.status,
                stacktrace=core.get_stacktrace(),
                link=e.link,
            )
        except MyappException as e:
            logging.exception(e)
            return json_error_response(
                core.error_msg_from_exception(e),
                stacktrace=core.get_stacktrace(),
                status=e.status,
            )
        except HTTPException as e:
            logging.exception(e)
            return json_error_response(
                core.error_msg_from_exception(e),
                stacktrace=traceback.format_exc(),
                status=e.code,
            )
        except Exception as e:
            logging.exception(e)
            return json_error_response(
                core.error_msg_from_exception(e), stacktrace=core.get_stacktrace()
            )

    return functools.update_wrapper(wraps, f)


# 获取用户的角色
def get_user_roles():
    if g.user.is_anonymous:
        return []
    return g.user.roles


class BaseMyappView(BaseView):
    # json响应
    def json_response(self, obj, status=200):
        return Response(
            json.dumps(obj, default=core.json_int_dttm_ser, ignore_nan=True),
            status=status,
            mimetype="application/json",
        )

    # 前端显示数据
    def common_bootstrap_payload(self):
        """Common data always sent to the client"""
        messages = get_flashed_messages(with_categories=True)
        locale = str(get_locale())
        return {
            "flash_messages": messages,
            "conf": {k: conf.get(k) for k in FRONTEND_CONF_KEYS},
            "locale": locale,
            "feature_flags": get_feature_flags(),
        }

    alert_config = {}  # url:function

    def __init__(self):
        super(BaseMyappView, self).__init__()

        if 'alert_config' not in conf:
            conf['alert_config'] = {}
        conf['alert_config'].update(self.alert_config)


from flask import (
    abort,
    flash,
    jsonify,
    make_response,
    redirect,
    request,
    session,
    url_for,
)


def validate_json(form, field):  # noqa
    try:
        json.loads(field.data)
    except Exception as e:
        logging.exception(e)
        raise Exception(__("json isn't valid"))


class YamlExportMixin(object):
    @action("yaml_export", "Export to YAML", "Export to YAML?", "fa-download")
    def yaml_export(self, items):
        if not isinstance(items, list):
            items = [items]

        data = [t.export_to_dict() for t in items]
        return Response(
            yaml.safe_dump(data),
            headers=generate_download_headers("yaml"),
            mimetype="application/text",
        )


# 列表页面删除/批量删除的操作
class DeleteMixin(object):
    def _delete(self, pk):
        """
            Delete function logic, override to implement diferent logic
            deletes the record with primary_key = pk

            :param pk:
                record primary key to delete
        """
        item = self.datamodel.get(pk, self._base_filters)
        if not item:
            abort(404)
        try:
            self.pre_delete(item)
        except Exception as e:
            flash(str(e), "error")
        else:
            view_menu = security_manager.find_view_menu(item.get_perm())
            pvs = (
                security_manager.get_session.query(security_manager.permissionview_model).filter_by(view_menu=view_menu).all()
            )

            schema_view_menu = None
            if hasattr(item, "schema_perm"):
                schema_view_menu = security_manager.find_view_menu(item.schema_perm)

                pvs.extend(
                    security_manager.get_session.query(security_manager.permissionview_model).filter_by(view_menu=schema_view_menu).all()
                )

            if self.datamodel.delete(item):
                self.post_delete(item)

                for pv in pvs:
                    security_manager.get_session.delete(pv)

                if view_menu:
                    security_manager.get_session.delete(view_menu)

                if schema_view_menu:
                    security_manager.get_session.delete(schema_view_menu)

                security_manager.get_session.commit()

            flash(*self.datamodel.message)
            self.update_redirect()

    @action("muldelete", "删除", "确定删除所选记录?", "fa-trash", single=False)
    def muldelete(self, items):
        if not items:
            abort(404)
        for item in items:
            try:
                self.pre_delete(item)
            except Exception as e:
                flash(str(e), "error")
            else:
                self._delete(item.id)
        self.update_redirect()
        return redirect(self.get_redirect())


# model list的过滤器
class MyappFilter(BaseFilter):
    """Add utility function to make BaseFilter easy and fast

    These utility function exist in the SecurityManager, but would do
    a database round trip at every check. Here we cache the role objects
    to be able to make multiple checks but query the db only once
    """

    def get_user_roles(self):
        return get_user_roles()

    def get_all_permissions(self):
        return set()

    def has_role(self, role_name_or_list):
        """Whether the user has this role name"""
        if not isinstance(role_name_or_list, list):
            role_name_or_list = [role_name_or_list]
        return any([r.name in role_name_or_list for r in self.get_user_roles()])

    def has_perm(self, permission_name, view_menu_name):
        return True

    # 获取所有绑定了指定权限的所有vm
    def get_view_menus(self, permission_name):
        return set()


# 检查是否有权限
def check_ownership(obj, raise_if_false=True):
    """Meant to be used in `pre_update` hooks on models to enforce ownership

    Admin have all access, and other users need to be referenced on either
    the created_by field that comes with the ``AuditMixin``, or in a field
    named ``owners`` which is expected to be a one-to-many with the User
    model. It is meant to be used in the ModelView's pre_update hook in
    which raising will abort the update.
    """
    if not obj:
        return False

    security_exception = MyappSecurityException(
        "You don't have the rights to alter [{}]".format(obj)
    )

    if g.user.is_anonymous:
        if raise_if_false:
            raise security_exception
        return False
    roles = [r.name for r in get_user_roles()]
    if "Admin" in roles:
        return True
    session = db.create_scoped_session()
    orig_obj = session.query(obj.__class__).filter_by(id=obj.id).first()

    # Making a list of owners that works across ORM models
    owners = []
    if hasattr(orig_obj, "owners"):
        owners += orig_obj.owners
    if hasattr(orig_obj, "owner"):
        owners += [orig_obj.owner]
    if hasattr(orig_obj, "created_by"):
        owners += [orig_obj.created_by]

    owner_names = [o.username for o in owners if o]

    if g.user and hasattr(g.user, "username") and g.user.username in owner_names:
        return True
    if raise_if_false:
        raise security_exception
    else:
        return False


# 绑定字段
def bind_field(self, form: DynamicForm, unbound_field: UnboundField, options: Dict[Any, Any]) -> Field:
    """
    Customize how fields are bound by stripping all whitespace.

    :param form: The form
    :param unbound_field: The unbound field
    :param options: The field options
    :returns: The bound field
    """

    filters = unbound_field.kwargs.get("filters", [])
    filters.append(lambda x: x.strip() if isinstance(x, str) else x)
    return unbound_field.bind(form=form, filters=filters, **options)


FlaskForm.Meta.bind_field = bind_field
