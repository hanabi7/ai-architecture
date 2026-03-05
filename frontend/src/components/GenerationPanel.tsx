import React, { useState, useEffect } from 'react';
import { Card, Image, Button, Radio, Spin, message, Tag } from 'antd';
import { ReloadOutlined, CheckOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { generateFromSketch } from '../api';

interface GenerationPanelProps {
  project: any;
  onComplete: (data: any) => void;
  onBack: () => void;
}

export const GenerationPanel: React.FC<GenerationPanelProps> = ({
  project,
  onComplete,
  onBack
}) => {
  const [images, setImages] = useState<any[]>([]);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    generateImages();
  }, []);

  const generateImages = async () => {
    setLoading(true);
    try {
      const result = await generateFromSketch({
        sketch_path: project.sketchUrl,
        prompt: project.prompt,
        style: project.style
      });

      if (result.success) {
        setImages(result.images);
        setSelectedImage(result.images[0]?.url);
      } else {
        message.error(result.error || '生成失败');
      }
    } catch (error) {
      message.error('生成请求失败');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = () => {
    if (!selectedImage) {
      message.warning('请选择一张效果图');
      return;
    }
    onComplete({
      selectedImage,
      images
    });
  };

  return (
    <div className="generation-panel">
      <div className="panel-header">
        <Button icon={<ArrowLeftOutlined />} onClick={onBack}>
          返回
        </Button>
        <Button
          icon={<ReloadOutlined />}
          onClick={generateImages}
          loading={loading}
        >
          重新生成
        </Button>
      </div>

      <div className="comparison-view">
        <Card title="原始草图" className="sketch-card">
          <Image
            src={project?.sketchUrl}
            alt="Sketch"
            style={{ maxHeight: '400px', objectFit: 'contain' }}
          />
        </Card>

        <Card 
          title="AI 生成的建筑效果图" 
          className="render-card"
          extra={loading && <Spin />}
        >
          {loading ? (
            <div className="loading-placeholder">
              <Spin size="large" />
              <p>AI 正在生成建筑效果图...⏳</p>
              <p className="hint">预计需要 30-60 秒</p>
            </div>
          ) : (
            <Radio.Group
              value={selectedImage}
              onChange={(e) => setSelectedImage(e.target.value)}
              className="image-selector"
            >
              <div className="generated-images">
                {images.map((img, index) => (
                  <div
                    key={index}
                    className={`image-option ${selectedImage === img.url ? 'selected' : ''}`}
                    onClick={() => setSelectedImage(img.url)}
                  >
                    <Radio value={img.url}></Radio>
                    <Image
                      src={img.url}
                      alt={`Generated ${index + 1}`}
                      preview={false}
                    />
                    <Tag className="provider-tag">{img.provider}</Tag>
                  </div>
                ))}
              </div>
            </Radio.Group>
          )}
        </Card>
      </div>

      {!loading && (
        <Button
          type="primary"
          size="large"
          icon={<CheckOutlined />}
          onClick={handleConfirm}
          block
          style={{ marginTop: 20 }}
        >
          确认选择，开始 3D 重建
        </Button>
      )}
    </div>
  );
};
