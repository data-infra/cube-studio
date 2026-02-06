import React, { useEffect, useState } from "react";
import { Row, Col, Typography, Spin, message } from "antd";
import {
  PlayCircleOutlined,
  FileTextOutlined,
  DeploymentUnitOutlined,
} from "@ant-design/icons";
import FeatureCard from "./components/FeatureCard";
import VideoCard from "./components/VideoCard";
import PipelineList from "./components/PipelineList";
import api from "../../api/index";
import "./Home.less";
import { useTranslation } from "react-i18next";

const { Title } = Typography;

interface VideoItem {
  name: string;
  img: string;
  video: string;
}

const Home: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [videoList, setVideoList] = useState<VideoItem[]>([]);

  // 加载数据
  useEffect(() => {
    loadHomeData();
  }, []);

  const loadHomeData = async () => {
    setLoading(true);

    try {
      // 设置视频列表
      setVideoList([
        {
          name: t('新人制作一个pipeline'),
          img: "/static/assets/images/ad/video-cover1-thumb.png",
          video:
            "https://cube-studio.oss-cn-hangzhou.aliyuncs.com/cube-studio.mp4",
        },
        {
          name: t('自定义任务模板'),
          img: "/static/assets/images/ad/video-cover2-thumb.png",
          video:
            "https://cube-studio.oss-cn-hangzhou.aliyuncs.com/job-template.mp4",
        },
      ]);
    } catch (error: any) {
      console.error("加载首页数据失败:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="home-loading">
        <Spin size="large" tip={t('加载中')} />
      </div>
    );
  }

  return (
    <div className="home-container">
      <div className="home-content">
        {/* 平台主要功能区 */}
        <section className="home-section">
          <div className="section-header">
            <Title level={5}>
              <DeploymentUnitOutlined /> {t('平台主要功能')}
            </Title>
          </div>
          <FeatureCard />
        </section>

        {/* 新手视频区 */}
        {videoList.length > 0 && (
          <section className="home-section">
            <div className="section-header">
              <Title level={5}>
                <PlayCircleOutlined /> {t('新手视频')}
              </Title>
            </div>
            <Row gutter={[12, 12]}>
              {videoList.map((video, index) => (
                <Col xs={12} sm={8} md={6} lg={4} xl={3} key={index}>
                  <VideoCard video={video} />
                </Col>
              ))}
            </Row>
          </section>
        )}

        {/* 流水线列表区 */}
        <section className="home-section">
          <div className="section-header">
            <Title level={5}>
              <FileTextOutlined /> {t('流水线')}
            </Title>
          </div>
          <PipelineList />
        </section>
      </div>
    </div>
  );
};

export default Home;
