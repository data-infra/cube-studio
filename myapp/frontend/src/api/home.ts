import api, { AxiosResFormat } from "./index";

/**
 * 获取平台主要功能-demo列表
 */
export const getDemoList = (params: any): AxiosResFormat<any> => {
  return api.get("/pipeline_modelview/api/demo/list/", {
    params,
    headers: { "X-Silent-Error": "true" },
  });
};

/**
 * 获取流水线列表
 * @param tab 标签类型：'my' | 'all'
 * @param page 页码（从 1 开始）
 * @param pageSize 每页条数
 */
export const getPipelineList = (
  tab: "my" | "all" = "my",
  page: number = 1,
  pageSize: number = 10
): AxiosResFormat<any> => {
  let url = "";
  let params: any = {};

  if (tab === "all") {
    // 协作标签：后端分页
    url = "/pipeline_modelview/home/api/";
    params = {
      form_data: JSON.stringify({
        page: page - 1, // 后端从 0 开始
        page_size: pageSize,
      }),
    };
  } else {
    // 我的标签
    url = "/pipeline_modelview/api/my/list/";
  }

  return api.get(url, { params, headers: { "X-Silent-Error": "true" } });
};

/**
 * 获取项目列表
 */
export const getProjectList = (): AxiosResFormat<any> => {
  return api.get("/project_modelview/api/");
};

/**
 * 创建新的流水线
 * @param data 流水线数据
 */
export const createPipeline = (data?: any): AxiosResFormat<any> => {
  return api.post("/pipeline_modelview/api/", data || {}, {
    headers: { "X-Silent-Error": "true" },
  });
};

/**
 * 删除流水线
 * @param id 流水线ID
 */
export const deletePipeline = (id: number): AxiosResFormat<any> => {
  return api.delete(`/pipeline_modelview/api/${id}`, {
    headers: { "X-Silent-Error": "true" },
  });
};

/**
 * 获取首页配置（功能卡片、视频列表）
 */
export const getHomeConfig = (): AxiosResFormat<any> => {
  return api.get("/myapp/home_config");
};

export default {
  getPipelineList,
  getProjectList,
  createPipeline,
  deletePipeline,
  getHomeConfig,
};
