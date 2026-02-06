import React, { useState } from "react";
import { Card, Modal, message } from "antd";
import { PlayCircleOutlined } from "@ant-design/icons";
import "./VideoCard.less";

interface VideoCardProps {
  video: {
    name: string;
    img: string;
    video: string;
  };
}

const VideoCard: React.FC<VideoCardProps> = ({ video }) => {
  console.log('video', video);
  const [modalVisible, setModalVisible] = useState(false);
  const [videoError, setVideoError] = useState(false);

  const handleClick = () => {
    setModalVisible(true);
    setVideoError(false);
  };

  const handleVideoError = () => {
    setVideoError(true);
    message.warning("视频加载失败，请稍后重试");
  };

  return (
    <>
      <Card
        hoverable
        className="video-card"
        onClick={handleClick}
        cover={
          <div className="video-card-cover">
            <img
              src={video.img}
              alt={video.name}
              onError={(e) => {
                // 图片加载失败时使用默认图片
                e.currentTarget.src = "/static/appbuilder/vison/logo.png";
              }}
            />
            <div className="video-play-overlay">
              <PlayCircleOutlined className="play-icon" />
            </div>
          </div>
        }
      >
        <Card.Meta title={video.name} />
      </Card>

      <Modal
        title={video.name}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={800}
        centered
        destroyOnClose
      >
        <div className="video-player">
          {videoError ? (
            <div
              style={{
                textAlign: "center",
                padding: "60px 20px",
                color: "#999",
              }}
            >
              <PlayCircleOutlined style={{ fontSize: 48, marginBottom: 16 }} />
              <div>视频暂时无法播放</div>
              <div style={{ fontSize: 12, marginTop: 8 }}>
                请检查网络连接或稍后重试
              </div>
            </div>
          ) : (
            <video
              src={video.video}
              controls
              autoPlay
              onError={handleVideoError}
              style={{ width: "100%", maxHeight: "500px", background: "#000" }}
            />
          )}
        </div>
      </Modal>
    </>
  );
};

export default VideoCard;
