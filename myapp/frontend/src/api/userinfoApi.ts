import api, { AxiosResFormat } from "./index";

export interface IUserInfo {
  username: string;
  nickname?: string;
  email: string;
  roles: string;
  active: boolean;
  org: string;
  quota?: string;
  secret?: string;
  balance?: string;
  created_on?: string;
  created_by?: string;
  changed_on?: string;
  changed_by?: string;
  wechat?: string;
  phone?: string;
  verified?: boolean;
}

/** _info 返回的单个校验规则 */
export interface IUserinfoValidator {
  type?: string;
  regex?: string;
  min?: number | null;
  max?: number | null;
  message?: string;
  [key: string]: unknown;
}

/**
 * _info 返回的列配置
 * - label: 列的中文名（与 label_columns 对应）
 * - description: 列的描述（与 description_columns 对应）
 */
export interface IUserinfoColumnInfo {
  name: string;
  label?: string;
  description?: string;
  type?: string;
  default?: unknown;
  disable?: boolean;
  required?: boolean;
  "ui-type"?: string;
  validators?: IUserinfoValidator[];
  [key: string]: unknown;
}

/**
 * _info 返回的完整配置
 * - label_columns: 列的中文名
 * - show_columns: 查看的列（详情展示）
 * - edit_columns: 可编辑列（编辑表单）
 * - description_columns: 列的描述（表单项下方提示）
 */
export interface IUserinfoInfo {
  show_columns: string[];
  edit_columns: IUserinfoColumnInfo[];
  add_columns?: IUserinfoColumnInfo[];
  label_columns: Record<string, string>;
  description_columns?: Record<string, unknown>;
  show_title?: string;
  edit_title?: string;
}

/**
 * 获取用户信息页的列配置（详情列、编辑列及其中文、描述等）
 */
export const getCurrentUserinfoInfo = (): AxiosResFormat<IUserinfoInfo> => {
  return api.get("/userinfo/api/_info");
};

/**
 * 获取当前用户个人信息
 */
export const getCurrentUserinfo = (): AxiosResFormat<IUserInfo> => {
  return api.get("/userinfo/api/current/userinfo");
};

/**
 * 更新当前用户个人信息
 */
export const updateCurrentUserinfo = (data: Partial<IUserInfo> & { password?: string }): AxiosResFormat<unknown> => {
  return api.post("/userinfo/api/current/userinfo", data);
};
