import React, { useEffect, useState } from "react";
import { Spin, message, Typography, Descriptions, Form, Input, Button, Space } from "antd";
import {
  CaretDownOutlined,
  EditOutlined,
  SaveOutlined,
  ArrowLeftOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from "@ant-design/icons";
import {
  getCurrentUserinfoInfo,
  getCurrentUserinfo,
  updateCurrentUserinfo,
  IUserInfo,
  IUserinfoInfo,
  IUserinfoColumnInfo,
  IUserinfoValidator,
} from "../../api/userinfoApi";
import { useTranslation } from "react-i18next";
import "./UserCenter.less";

const { Title, Text } = Typography;

function getEmptyPlaceholder(t: (key: string) => string): string {
  return t("空描述") || "—";
}

function displayValue(v: unknown, emptyStr: string): string {
  if (v === null || v === undefined || v === "") return emptyStr;
  if (typeof v === "boolean") return v ? "True" : "False";
  const s = String(v).trim();
  return s === "" ? emptyStr : s;
}

/** 校验无 message/description 时的默认提示 */
const DEFAULT_VALIDATE_MSG = "请按正确的规则输入";

/**
 * 根据 _info 返回的 validators 校验单个字段（后端自定义规则）
 * 空值（DataRequired）时优先提示「请输入{label}」，否则用 validator.message 或 description
 */
function validateField(
  value: string,
  validators: IUserinfoValidator[] | undefined,
  options: { description?: string; label?: string }
): string | null {
  if (!validators || !Array.isArray(validators) || validators.length === 0) return null;
  const str = value == null ? "" : String(value).trim();
  const rawLabel = options.label != null ? String(options.label).trim() : "";
  for (const v of validators) {
    const type = (v.type as string) || "";
    let invalid = false;
    if (type === "DataRequired") {
      invalid = str === "";
    } else if (type === "Regexp" && v.regex) {
      try {
        invalid = !new RegExp(v.regex as string).test(str);
      } catch {
        continue;
      }
    } else {
      continue;
    }
    if (invalid) {
      if (type === "DataRequired" && str === "") {
        return rawLabel ? `请输入${rawLabel}` : "请填写";
      }
      return DEFAULT_VALIDATE_MSG;
    }
  }
  return null;
}

const UserCenter: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [infoConfig, setInfoConfig] = useState<IUserinfoInfo | null>(null);
  const [info, setInfo] = useState<IUserInfo | null>(null);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    loadInfoConfigAndUserinfo();
  }, []);

  const loadInfoConfigAndUserinfo = async () => {
    setLoading(true);
    try {
      const [infoRes, dataRes] = await Promise.all([
        getCurrentUserinfoInfo(),
        getCurrentUserinfo(),
      ]);
      const configRaw = infoRes?.data?.result ?? infoRes?.data ?? infoRes?.data?.data ?? infoRes?.data;
      const dataRaw = dataRes?.data?.result ?? dataRes?.data ?? dataRes?.data?.data ?? dataRes?.data;
      const config = (typeof configRaw === "object" && configRaw !== null ? configRaw : {}) as IUserinfoInfo;
      const data = (typeof dataRaw === "object" && dataRaw !== null ? dataRaw : {}) as IUserInfo;
      setInfoConfig({
        show_columns: config.show_columns || [],
        edit_columns: config.edit_columns || [],
        label_columns: config.label_columns || {},
        description_columns: config.description_columns || {},
        show_title: config.show_title,
        edit_title: config.edit_title,
      });
      setInfo(data as IUserInfo);
      const initial: Record<string, string> = {};
      (config.edit_columns || []).forEach((col) => {
        const key = col.name;
        const val = (data as unknown as Record<string, unknown>)[key];
        initial[key] = val != null && val !== "" ? String(val) : "";
      });
      setFormValues(initial);
    } catch (e) {
      message.error(t("加载用户信息失败") || "加载用户信息失败");
    } finally {
      setLoading(false);
    }
  };

  const loadUserinfo = async () => {
    try {
      const res = await getCurrentUserinfo();
      const dataRaw = res?.data?.result ?? res?.data ?? res?.data?.data ?? res?.data;
      const data = (typeof dataRaw === "object" && dataRaw !== null ? dataRaw : {}) as IUserInfo;
      setInfo(data);
      const initial: Record<string, string> = {};
      (infoConfig?.edit_columns || []).forEach((col) => {
        const key = col.name;
        const val = (data as unknown as Record<string, unknown>)[key];
        initial[key] = val != null && val !== "" ? String(val) : "";
      });
      setFormValues(initial);
    } catch (e) {
      message.error(t("加载用户信息失败") || "加载用户信息失败");
    }
  };

  const handleSaveEdit = async () => {
    if (!infoConfig) return;
    const descColMap = infoConfig.description_columns || {};
    const getDesc = (name: string, col: IUserinfoColumnInfo) => {
      const fromCol = descColMap[name];
      if (fromCol != null && fromCol !== "") return String(fromCol);
      return (col.description as string) ?? "";
    };
    const errors: Record<string, string> = {};
    let firstError: string | null = null;
    for (const col of infoConfig.edit_columns || []) {
      const key = col.name;
      let value = formValues[key] ?? "";
      if (key === "password") {
        if (value.trim()) value = value.trim();
        else continue;
      } else {
        value = value.trim();
      }
      const label =
        (col.label != null && String(col.label).trim()) ||
        infoConfig.label_columns?.[key] ||
        key;
      const err = validateField(value, col.validators, {
        description: getDesc(key, col),
        label,
      });
      if (err != null && err !== "") {
        errors[key] = err;
        if (!firstError) firstError = err;
      }
    }
    if (firstError) {
      setFieldErrors(errors);
      return;
    }
    setFieldErrors({});
    const payload: Record<string, unknown> = {};
    (infoConfig?.edit_columns || []).forEach((col) => {
      const key = col.name;
      if (key === "password") {
        const v = formValues[key];
        if (v && v.trim()) payload[key] = v.trim();
        return;
      }
      payload[key] = formValues[key]?.trim() ?? "";
    });
    setSaving(true);
    try {
      await updateCurrentUserinfo(payload as Partial<IUserInfo> & { password?: string });
      message.success(t("保存成功") || "保存成功");
      setIsEditMode(false);
      loadUserinfo();
    } catch (e) {
      message.error(t("保存失败") || "保存失败");
    } finally {
      setSaving(false);
    }
  };

  /** 根据当前表单值对全部字段做一次校验，用于进入编辑时展示错误（含未改动的邮箱等） */
  const validateAllFields = (values: Record<string, string>): Record<string, string> => {
    if (!infoConfig) return {};
    const descColMap = infoConfig.description_columns || {};
    const getDesc = (n: string, c: IUserinfoColumnInfo) => {
      const fromCol = descColMap[n];
      if (fromCol != null && fromCol !== "") return String(fromCol);
      return (c.description as string) ?? "";
    };
    const errors: Record<string, string> = {};
    for (const col of infoConfig.edit_columns || []) {
      const key = col.name;
      let value = values[key] ?? "";
      if (key === "password") {
        if (!value.trim()) continue;
        value = value.trim();
      } else {
        value = value.trim();
      }
      const label =
        (col.label != null && String(col.label).trim()) ||
        infoConfig.label_columns?.[key] ||
        key;
      const err = validateField(value, col.validators, {
        description: getDesc(key, col),
        label,
      });
      if (err) errors[key] = err;
    }
    return errors;
  };

  const setFormValue = (name: string, value: string) => {
    setFormValues((prev) => ({ ...prev, [name]: value }));
    if (!infoConfig) return;
    const col = infoConfig.edit_columns?.find((c) => c.name === name);
    if (!col) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
      return;
    }
    const descColMap = infoConfig.description_columns || {};
    const getDesc = (n: string, c: IUserinfoColumnInfo) => {
      const fromCol = descColMap[n];
      if (fromCol != null && fromCol !== "") return String(fromCol);
      return (c.description as string) ?? "";
    };
    let val = value;
    if (name === "password") {
      if (val.trim() === "") {
        setFieldErrors((prev) => ({ ...prev, [name]: "" }));
        return;
      }
      val = val.trim();
    } else {
      val = value.trim();
    }
    const label =
      (col.label != null && String(col.label).trim()) ||
      infoConfig.label_columns?.[name] ||
      name;
    const err = validateField(val, col.validators, {
      description: getDesc(name, col),
      label,
    });
    setFieldErrors((prev) => ({ ...prev, [name]: err || "" }));
  };

  /** 退出编辑 */
  const handleCancelEdit = () => {
    if (infoConfig && info) {
      const initial: Record<string, string> = {};
      (infoConfig.edit_columns || []).forEach((col) => {
        const key = col.name;
        const val = (info as unknown as Record<string, unknown>)[key];
        initial[key] = val != null && val !== "" ? String(val) : "";
      });
      setFormValues(initial);
    }
    setFieldErrors({});
    setIsEditMode(false);
  };

  if (loading || !infoConfig) {
    return (
      <div className="user-center">
        <div className="user-center-inner user-center-loading">
          <Spin size="large" tip={t("加载中") || "加载中"} />
        </div>
      </div>
    );
  }

  const emptyStr = getEmptyPlaceholder(t);
  // label_columns: 列的中文名
  const labelCol = infoConfig.label_columns || {};
  // description_columns: 列的描述
  const descCol = infoConfig.description_columns || {};
  // show_columns: 查看的列（详情展示）
  const showColumns = infoConfig.show_columns || [];
  // edit_columns: 可编辑列（编辑表单）
  const editColumns = infoConfig.edit_columns || [];

  const getLabel = (name: string, col?: IUserinfoColumnInfo) =>
    col?.label ?? labelCol[name] ?? name;

  const getDescription = (name: string, col?: IUserinfoColumnInfo): string => {
    const fromDescCol = descCol[name];
    if (fromDescCol != null && fromDescCol !== "") return String(fromDescCol);
    return (col?.description as string) ?? "";
  };

  const renderDetailValue = (colName: string, value: unknown) => {
    if (colName === "active") {
      if (value === true) {
        return <CheckCircleOutlined style={{ color: "#52c41a", fontSize: 18 }} />;
      }
      if (value === false) {
        return <CloseCircleOutlined style={{ color: "#ff4d4f", fontSize: 18 }} />;
      }
      return <Text type="secondary">{emptyStr}</Text>;
    }
    if (colName === "roles" && value != null && value !== "") {
      return <Text type={value ? undefined : "secondary"}>{`[${value}]`}</Text>;
    }
    if (colName === "secret") {
      return (
        <Text type="secondary" copyable={!!value} style={{ wordBreak: "break-all" }}>
          {displayValue(value, emptyStr)}
        </Text>
      );
    }
    return (
      <Text type={value != null && value !== "" ? undefined : "secondary"}>
        {displayValue(value, emptyStr)}
      </Text>
    );
  };

  // 编辑用户信息表单（按 edit_columns 可编辑列 渲染，标签用 label_columns 列的中文名，描述用 description_columns 列的描述）
  if (isEditMode) {
    const editTitle = infoConfig.edit_title || t("编辑用户信息") || "编辑用户信息";
    return (
      <div className="user-center">
        <div className="user-center-inner">
          <Title level={5} className="page-title">
            {editTitle}
            <CaretDownOutlined className="title-caret" />
          </Title>
          {editColumns.map((col) => {
            const name = col.name;
            const label = getLabel(name, col);
            const desc = getDescription(name, col);
            const isPassword = name === "password";
            const disabled = !!col.disable;
            const required = col.required === true;
            return (
              <div key={name} className="form-row">
                <div className="label-col">
                  <span className="label-required-slot">
                    {required ? <Text type="danger">*</Text> : null}
                  </span>
                  {label}:
                </div>
                <div className="value-col">
                  <Form.Item
                    validateStatus={fieldErrors[name] ? "error" : undefined}
                    style={{ marginBottom: 0 }}
                  >
                    {isPassword ? (
                      <Input.Password
                        value={formValues[name] ?? ""}
                        onChange={(e) => setFormValue(name, e.target.value)}
                        placeholder={t("留空则不修改密码") || "留空则不修改密码"}
                        autoComplete="new-password"
                        disabled={disabled}
                        allowClear
                      />
                    ) : (
                      <Input
                        value={formValues[name] ?? ""}
                        onChange={(e) => setFormValue(name, e.target.value)}
                        placeholder={label}
                        disabled={disabled}
                        allowClear
                        type="text"
                      />
                    )}
                  </Form.Item>
                  <div className="form-extra-row">
                    {fieldErrors[name] ? (
                      <div className="form-error">
                        <Text type="danger">{fieldErrors[name]}</Text>
                      </div>
                    ) : null}
                    {desc ? (
                      <div
                        className="form-hint"
                        dangerouslySetInnerHTML={{ __html: desc }}
                      />
                    ) : null}
                  </div>
                </div>
              </div>
            );
          })}
          <div className="btn-row">
            <Space>
              <Button icon={<ArrowLeftOutlined />} onClick={handleCancelEdit}>
                {t("返回") || "返回"}
              </Button>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSaveEdit}
                loading={saving}
              >
                {saving ? t("保存中") || "保存中" : t("保存") || "保存"}
              </Button>
            </Space>
          </div>
        </div>
      </div>
    );
  }

  // 用户信息展示（按 show_columns 查看的列 渲染，标签用 label_columns 列的中文名）
  const showTitle = infoConfig.show_title || t("用户信息") || "用户信息";
  return (
    <div className="user-center">
      <div className="user-center-inner">
        <Title level={5} className="page-title">
          {showTitle}
          <CaretDownOutlined className="title-caret" />
        </Title>
        <Descriptions column={1} bordered size="small" className="user-center-descriptions">
          {showColumns.map((colName) => {
            const value = info ? (info as unknown as Record<string, unknown>)[colName] : undefined;
            const label = getLabel(colName);
            return (
              <Descriptions.Item key={colName} label={label}>
                {renderDetailValue(colName, value)}
              </Descriptions.Item>
            );
          })}
        </Descriptions>
        <div className="btn-row">
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={() => {
              setFieldErrors(validateAllFields(formValues));
              setIsEditMode(true);
            }}
          >
            {t("编辑用户") || "编辑用户"}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default UserCenter;
