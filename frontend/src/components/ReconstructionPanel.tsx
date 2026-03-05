import React, { useState } from 'react';
import { Card, Button, Radio, Spin, Progress, message } from 'antd';
import { ArrowLeftOutlined, CheckOutlined, LoadingOutlined } from '@ant-design/icons';
import { startReconstruction, getReconstructionStatus } from '../api';
import './ReconstructionPanel.css';

interface ReconstructionPanelProps {
  project: any;
  onComplete: (data: any) => void;
  onBack: () => void;
}

export const ReconstructionPanel: React.FC<ReconstructionPanelProps> = ({
  project,
  onComplete,
  onBack
}) => {
  const [method, setMethod] = useState('luma');
  const [status, setStatus] = useState<'idle' | 'processing' | 'completed' | 'failed'>('idle');
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<any>(null);

  const startReconstructionProcess = async () => {
    setStatus('processing');
    setProgress(0);

    try {
      // 1. 启动重建任务
      const job = await startReconstruction({
        image_url: project.renderUrl,
        method: method,
        quality: 'high'
      });

      // 2. 轮询状态
      const pollStatus = async () => {
        const statusData = await getReconstructionStatus(job.job_id);

        if (statusData.status === 'completed') {
          setStatus('completed');
          setResult(statusData);
          
          // 获取材质信息
          // const materials = await analyzeMaterials(project.renderUrl);
          
          onComplete({
            modelUrl: statusData.model_url,
            materials: [] // materials.materials
          });
        } else if (statusData.status === 'failed') {
          setStatus('failed');
          message.error('3D 重建失败: ' + statusData.error);
        } else {
          // 继续轮询
          setProgress(statusData.progress || 0);
          setTimeout(pollStatus, 5000);
        }
      };

      pollStatus();

    } catch (error: any) {
      setStatus('failed');
      message.error('启动重建失败: ' + error.message);
    }
  };

  return (
    <div className="reconstruction-panel">
      <div className="panel-header">
        <Button icon={<ArrowLeftOutlined />} onClick={onBack}>
          返回
        </Button>
      </div>

      <Card title="🎨 选中的建筑效果图">
        <img
          src={project?.renderUrl}
          alt="Selected Render"
          style={{ maxWidth: '100%', maxHeight: '300px' }}
        />
      </Card>

      <Card title="🔧 选择 3D 重建方案" style={{ marginTop: 20 }}>
        <Radio.Group
          value={method}
          onChange={(e) => setMethod(e.target.value)}
          disabled={status === 'processing'}
        >
          <Radio.Button value="luma">
            ⚡ Luma AI (云端快速)
            <br />
            <small>$5/次 · 10-30 分钟 · 高质量</small>
          </Radio.Button>
          <Radio.Button value="wonder3d">
            🖥️ 本地训练 (免费)
            <br />
            <small>需 GPU · 1-4 小时 · 可定制</small>
          </Radio.Button>
        </Radio.Group>

        {status === 'idle' && (
          <Button
            type="primary"
            size="large"
            onClick={startReconstructionProcess}
            block
            style={{ marginTop: 20 }}
          >
            开始 3D 重建
          </Button>
        )}

        {status === 'processing' && (
          <div className="processing-status">
            <Spin indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />} />
            <p>正在进行 3D 重建...🔄</p>
            <Progress percent={progress} status="active" />
            <p className="hint">
              {method === 'luma' 
                ? '使用 Luma AI 云端服务，预计 10-30 分钟' 
                : '本地训练 Gaussian Splatting，预计 1-4 小时'}
            </p>
          </div>
        )}

        {status === 'completed' && (
          <div className="completed-status">
            <CheckOutlined style={{ fontSize: 48, color: '#52c41a' }} />
            <p>3D 重建完成！✅</p>
            <Button
              type="primary"
              size="large"
              onClick={() => onComplete(result)}
              block
            >
              查看 3D 模型
            </Button>
          </div>
        )}

        {status === 'failed' && (
          <div className="failed-status">
            <p>重建失败，请重试</p>
            <Button onClick={() => setStatus('idle')}>
              重试
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};
