import React, { useEffect, useState } from "react";
import { Card, Tabs, Table, message, Button } from "antd";
import type { ColumnsType } from "antd/es/table";
import {
  getPipelineList,
  getProjectList,
  deletePipeline,
} from "../../../api/home";
import dayjs from "dayjs";
import { DeleteOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";

const { TabPane } = Tabs;

interface Pipeline {
  id: number;
  name: string;
  describe: string;
  changed_on: string;
  project_id: number;
  creator: string;
}

interface Project {
  id: number;
  name: string;
}

const PipelineList: React.FC = () => {
  const { t } = useTranslation();
  const [pipelineList, setPipelineList] = useState<Pipeline[]>([]);
  const [projectList, setProjectList] = useState<Record<number, Project>>({});
  const [activeTab, setActiveTab] = useState("my");
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });

  // 表格列定义
  const getColumns = (): ColumnsType<Pipeline> => {
    const baseColumns: ColumnsType<Pipeline> = [
      {
        title: "ID",
        dataIndex: "id",
        key: "id",
        width: 80,
      },
      {
        title: "任务流",
        dataIndex: "name",
        key: "name",
        width: 250,
        render: (text: string, record: any) => {
          // "协作"标签：数据在 pipeline_url 字段中（HTML格式）
          // "我的"标签：数据在 name 字段中
          let name = "";
          let displayHtml = "";

          if (record.pipeline_url) {
            // 协作标签：从 pipeline_url 中提取名称
            // 格式: <a target=_blank href="/pipeline_modelview/api/web/5">任务流名称</a>
            const match = record.pipeline_url.match(/>([^<]+)</);
            name = match ? match[1] : "";
            displayHtml = name;
          } else {
            // 我的标签：直接使用 name 字段
            name = text || record.name || "";
            displayHtml = name;
          }

          if (!name) {
            return <span style={{ color: "#999" }}>-</span>;
          }

          return (
            <a
              href={`/frontend/showOutLink?url=${encodeURIComponent(
                `${window.location.origin}/static/appbuilder/vison/index.html?pipeline_id=${record.id}`
              )}`}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#1890ff" }}
              dangerouslySetInnerHTML={{ __html: displayHtml }}
            />
          );
        },
      },
      {
        title: t('描述'),
        dataIndex: "describe",
        key: "describe",
        ellipsis: true,
        render: (text: string) => (text ? t(text) : "-"),
      },
      {
        title: t('修改时间'),
        dataIndex: "changed_on",
        key: "changed_on",
        width: 220,
        render: (text: string) => {
          return <span>{dayjs(text).format("YYYY-MM-DD HH:mm:ss")}</span>;
        },
      },
      {
        title: t('项目组'),
        key: "project",
        width: 150,
        render: (_, record: any) => {
          // 从不同的字段获取项目ID
          const projectId = record.project_id || record.project?.id;
          if (projectId && projectList[projectId]) {
            return projectList[projectId].name;
          }
          // 如果有 project 对象且包含 name
          if (record.project?.name) {
            return record.project.name;
          }
          return "-";
        },
      },
    ];

    // 只在"我的"标签显示删除操作
    if (activeTab === "my") {
      baseColumns.push({
        title: t('操作'),
        key: "action",
        width: 120,
        align: "center",
        render: (_, record: Pipeline) => (
          <Button
            className="c-red"
            type="link"
            onClick={() => handleDeletePipeline(record)}
          >
            <DeleteOutlined /> {t('删除')}
          </Button>
        ),
      });
    }

    return baseColumns;
  };

  // 加载项目列表和流水线数据
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async (
    page = pagination.current,
    pageSize = pagination.pageSize,
    tab = activeTab
  ) => {
    setLoading(true);
    try {
      // 加载项目列表（只在第一次加载）
      if (Object.keys(projectList).length === 0) {
        try {
          const { data: projectData } = await getProjectList();
          if (projectData?.status === 0) {
            const projects: Record<number, Project> = {};
            const projectArray =
              projectData.result?.data || projectData.result || [];
            projectArray.forEach((project: Project) => {
              projects[project.id] = project;
            });
            setProjectList(projects);
          }
        } catch (err) {
          console.error("加载项目列表失败:", err);
        }
      }

      // 加载流水线列表（支持分页）
      try {
        const { data } = await getPipelineList(
          tab as "my" | "all",
          page,
          pageSize
        );

        if (data?.status === 0) {
          if (tab === "all") {
            // 协作标签：后端分页
            const result = data.result || {};
            const list = result.data || [];
            const count = result.count || 0;

            setPipelineList(list);
            setPagination({
              current: page,
              pageSize: pageSize,
              total: count,
            });
          } else {
            // 我的标签：前端分页
            const list = data.result || [];
            setPipelineList(list);
            setPagination({
              current: page,
              pageSize: pageSize,
              total: list.length,
            });
          }
        }
      } catch (err) {
        console.error("加载流水线失败:", err);
      }
    } catch (error) {
      console.error("加载流水线数据失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePipeline = async (record: Pipeline) => {
    try {
      const { data } = await deletePipeline(record.id);
      if (data?.status === 0) {
        message.success("删除成功");
        setPipelineList(pipelineList.filter((item) => item.id !== record.id));
      }
    } catch (err) {
      console.error("删除流水线失败:", err);
      message.error("删除失败");
    }
  };

  const handleTabChange = async (key: string) => {
    setActiveTab(key);
    setPagination({
      current: 1,
      pageSize: 10,
      total: 0,
    });
    loadData(1, 10, key);
  };

  const handleTableChange = (paginationConfig: any) => {
    loadData(paginationConfig.current, paginationConfig.pageSize);
  };

  return (
    <Card>
      <Tabs activeKey={activeTab} onChange={handleTabChange}>
        <TabPane tab={t('我的')} key="my">
          <Table
            columns={getColumns()}
            dataSource={pipelineList}
            rowKey="id"
            loading={loading}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: pagination.total,
              showSizeChanger: true,
              showQuickJumper: true,
              pageSizeOptions: ["10", "20", "50", "100"],
              showTotal: (total) => `${t('共')} ${total} ${t('条')}`,
            }}
            onChange={handleTableChange}
          />
        </TabPane>
        <TabPane tab={t('协作')} key="all">
          <Table
            columns={getColumns()}
            dataSource={pipelineList}
            rowKey="id"
            loading={loading}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: pagination.total,
              showSizeChanger: true,
              showQuickJumper: true,
              pageSizeOptions: ["10", "20", "50", "100"],
              showTotal: (total) => `共 ${total} 条`,
            }}
            onChange={handleTableChange}
          />
        </TabPane>
      </Tabs>
    </Card>
  );
};

export default PipelineList;
