import React, { useEffect, useState } from "react";
import { Card, Row, Col, message } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import "./FeatureCard.less";
import { getDemoList, createPipeline } from "../../../api/home";
import { useTranslation } from "react-i18next";

interface FeatureItem {
  name: string;
  img: string;
  type: string;
  args?: any;
}

const FeatureCard: React.FC = () => {
  const [featureList, setFeatureList] = useState<FeatureItem[]>([]);
  const [loading, setLoading] = useState(true);
  const { t } = useTranslation();

  useEffect(() => {
    loadFeatureList();
  }, []);

  const loadFeatureList = async () => {
    try {
      setLoading(true);
      // 使用静默模式获取 demo 列表
      const { data } = await getDemoList({ page: 0, page_size: 1000 });
      if (data?.status === 0) {
        const features = (data.result || []).map((item: any) => {
          try {
            const param = JSON.parse(item.parameter || "{}");
            return {
              name: item.describe || item.name,
              img: param.img || "/static/appbuilder/vison/logo.png",
              type: "pipeline",
              args: { pipeline_id: item.id },
            };
          } catch (e) {
            return {
              name: item.describe || item.name,
              img: "/static/appbuilder/vison/logo.png",
              type: "pipeline",
              args: { pipeline_id: item.id },
            };
          }
        });
        setFeatureList(features);
      }
    } catch (err) {
      console.error("加载Demo失败:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePipeline = async () => {
    try {
      const timestamp = Date.now();
      // 创建新的流水线（需要提供完整的必需字段）
      const { data } = await createPipeline({
        name: `admin-pipeline-${timestamp}`,
        describe: `new-pipeline-${timestamp}`,
        node_selector: "cpu=true;train=true",
        schedule_type: "once",
        image_pull_policy: "Always",
        parallelism: 1,
        project: 1, // 默认项目ID，可以根据实际情况调整
      });

      if (data?.status === 0 && data?.result?.id) {
        const pipelineId = data.result.id;
        // 跳转到编辑页面
        const url = `/frontend/showOutLink?url=${encodeURIComponent(
          `${window.location.origin}/static/appbuilder/vison/index.html?pipeline_id=${pipelineId}`
        )}`;
        window.open(url, "_blank");
      } else {
        message.error("创建流水线失败");
      }
    } catch (err) {
      console.error("创建流水线失败:", err);
      message.error("创建流水线失败");
    }
  };

  const handleCardClick = (feature: FeatureItem) => {
    if (feature.type === "link" && feature.args?.url) {
      // 打开外部链接
      if (feature.args.url.startsWith("http")) {
        window.open(feature.args.url, "_blank");
      } else {
        // 内部路由
        window.location.href = feature.args.url;
      }
    } else if (feature.type === "pipeline" && feature.args?.pipeline_id) {
      // 打开pipeline编辑页面
      const url = `/frontend/showOutLink?url=${encodeURIComponent(
        `${window.location.origin}/static/appbuilder/vison/index.html?pipeline_id=${feature.args.pipeline_id}`
      )}`;
      window.open(url, "_blank");
    }
  };

  return (
    <Row gutter={[12, 12]}>
      {/* 新建流水线卡片 */}
      <Col xs={12} sm={8} md={6} lg={4} xl={3} className="home-card-col">
        <Card
          hoverable
          className="create-card"
          onClick={handleCreatePipeline}
          loading={loading}
        >
          <div className="card-content">
            <PlusOutlined className="create-icon" />
            <div className="card-title">{t('创建流水线')}</div>
          </div>
        </Card>
      </Col>

      {/* 功能卡片 */}
      {featureList.map((feature, index) => (
        <Col xs={12} sm={8} md={6} lg={4} xl={3} key={index} className="home-card-col">
          <Card
            hoverable
            className="feature-card"
            onClick={() => handleCardClick(feature)}
            cover={
              feature.img ? (
                <div className="feature-card-image">
                  <img src={feature.img} alt={feature.name} />
                </div>
              ) : null
            }
          >
            {/* 超出隐藏并显示省略号 */}
            <Card.Meta
              title={
                <div className="feature-card-title">
                  {feature.name ? t(feature.name) : "-"}
                </div>
              }
            />
          </Card>
        </Col>
      ))}
    </Row>
  );
};

export default FeatureCard;
