import { useState } from 'react';
import { Layout, Steps, Card, message } from 'antd';
import { 
  EditOutlined, 
  PictureOutlined, 
  BoxPlotOutlined, 
  EyeOutlined 
} from '@ant-design/icons';
import { SketchUploader } from './components/SketchUploader';
import { GenerationPanel } from './components/GenerationPanel';
import { ReconstructionPanel } from './components/ReconstructionPanel';
import { Viewer3D } from './components/Viewer3D';
import { useProjectStore } from './store/projectStore';
import './App.css';

const { Header, Content } = Layout;

// 步骤定义
const steps = [
  {
    title: '上传草图',
    icon: <EditOutlined />,
    description: '上传建筑草图'
  },
  {
    title: 'AI 生图',
    icon: <PictureOutlined />,
    description: '生成建筑效果图'
  },
  {
    title: '3D 重建',
    icon: <BoxPlotOutlined />,
    description: '生成 3D 模型'
  },
  {
    title: '可视化',
    icon: <EyeOutlined />,
    description: '交互展示'
  }
];

function App() {
  const [currentStep, setCurrentStep] = useState(0);
  const { project, setProject, updateProject } = useProjectStore();

  // 步骤 1: 草图上传完成
  const handleSketchUploaded = (projectData: any) => {
    setProject(projectData);
    setCurrentStep(1);
    message.success('草图上传成功，开始生成效果图');
  };

  // 步骤 2: 效果图生成完成
  const handleGenerationComplete = (renderData: any) => {
    updateProject({
      renderUrl: renderData.selectedImage,
      generatedImages: renderData.images
    });
    setCurrentStep(2);
    message.success('效果图生成成功，开始 3D 重建');
  };

  // 步骤 3: 3D 重建完成
  const handleReconstructionComplete = (modelData: any) => {
    updateProject({
      model3dUrl: modelData.modelUrl,
      materials: modelData.materials
    });
    setCurrentStep(3);
    message.success('3D 模型生成成功');
  };

  // 渲染当前步骤的内容
  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <SketchUploader 
            onUploadSuccess={handleSketchUploaded} 
          />
        );
      case 1:
        return (
          <GenerationPanel
            project={project}
            onComplete={handleGenerationComplete}
            onBack={() => setCurrentStep(0)}
          />
        );
      case 2:
        return (
          <ReconstructionPanel
            project={project}
            onComplete={handleReconstructionComplete}
            onBack={() => setCurrentStep(1)}
          />
        );
      case 3:
        return (
          <Viewer3D
            project={project}
            onRestart={() => {
              setProject(null);
              setCurrentStep(0);
            }}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Layout className="app-layout">
      <Header className="app-header">
        <div className="header-title">
          <h1>🏗️ AI 建筑可视化</h1>
          <p>草图 → AI 效果图 → 3D 模型 → Web 展示</p>
        </div>
      </Header>
      
      <Content className="app-content">
        <Card className="steps-card">
          <Steps
            current={currentStep}
            items={steps}
            direction="horizontal"
          />
        </Card>

        <div className="step-content">
          {renderStepContent()}
        </div>
      </Content>
    </Layout>
  );
}

export default App;
