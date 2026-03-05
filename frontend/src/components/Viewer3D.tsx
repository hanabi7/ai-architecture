import { useState } from 'react';
import { Card, Button, Tabs, Descriptions, Tag, Progress, Row, Col } from 'antd';
import { 
  ReloadOutlined, 
  DownloadOutlined,
  ExperimentOutlined,
  SafetyOutlined,
  DollarOutlined
} from '@ant-design/icons';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, ContactShadows } from '@react-three/drei';
import { GaussianSplatMesh } from './GaussianSplatMesh';
import { MapContainer, TileLayer, Marker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './Viewer3D.css';

interface Viewer3DProps {
  project: any;
  onRestart: () => void;
}

export const Viewer3D: React.FC<Viewer3DProps> = ({ project, onRestart }) => {
  const [selectedMaterial, setSelectedMaterial] = useState<any>(null);

  // 示例材质数据 (实际应从后端获取)
  const materials = project?.materials || [
    {
      id: 'mat-001',
      name: '清水混凝土',
      type: 'concrete',
      properties: { color: '#F5F5DC', roughness: 0.8, metallic: 0.0 },
      sustainability: 0.85,
      durability: 0.95,
      cost: 0.7,
      description: '裸露的混凝土表面，展现材料本真质感',
      location: '主体墙面'
    },
    {
      id: 'mat-002',
      name: '超白玻璃幕墙',
      type: 'glass',
      properties: { color: '#E0F6FF', roughness: 0.05, metallic: 0.1 },
      sustainability: 0.75,
      durability: 0.8,
      cost: 0.85,
      description: '高透光率玻璃，最大限度引入自然光',
      location: '采光立面'
    },
    {
      id: 'mat-003',
      name: '耐候钢板',
      type: 'steel',
      properties: { color: '#8B4513', roughness: 0.9, metallic: 0.6 },
      sustainability: 0.9,
      durability: 0.9,
      cost: 0.75,
      description: '表面形成稳定锈蚀层，具有独特的时间质感',
      location: '装饰构件'
    }
  ];

  // 示例位置数据
  const locationData = {
    name: '杭州西湖文化区',
    address: '浙江省杭州市西湖区',
    coordinates: { lat: 30.25, lng: 120.15 },
    climate: {
      type: '亚热带季风气候',
      temperature: { min: 4, max: 33 },
      humidity: 75,
      precipitation: 1450
    },
    sunlight: {
      direction: '东南向',
      hours: 6.5
    },
    context: '位于西湖风景区边缘，周边有传统江南园林和现代商业区'
  };

  const materialTypeColors: Record<string, string> = {
    concrete: '#8B8680',
    glass: '#87CEEB',
    steel: '#4682B4',
    wood: '#DEB887',
    stone: '#808080',
    composite: '#9370DB'
  };

  const materialTypeLabels: Record<string, string> = {
    concrete: '混凝土',
    glass: '玻璃',
    steel: '钢材',
    wood: '木材',
    stone: '石材',
    composite: '复合材料'
  };

  return (
    <div className="viewer-3d-container">
      <Row gutter={[16, 16]}>
        {/* 左侧：3D 模型展示 */}
        <Col span={16}>
          <Card 
            title="🏗️ 3D 建筑模型"
            className="viewer-3d-card"
            extra={
              <div className="viewer-controls">
                <Button icon={<DownloadOutlined />}>下载模型</Button>
                <Button icon={<ReloadOutlined />} onClick={onRestart}>新建项目</Button>
              </div>
            }
          >
            <div className="canvas-container" style={{ height: '600px' }}>
              <Canvas camera={{ position: [5, 5, 5], fov: 50 }}>
                <ambientLight intensity={0.5} />
                <directionalLight position={[10, 10, 5]} intensity={1} />
                
                {/* Gaussian Splatting 模型 */}
                <GaussianSplatMesh 
                  url={project?.model3dUrl || '/mock/model.splat'}
                />
                
                {/* 环境 */}
                <Environment preset="city" />
                <ContactShadows 
                  opacity={0.4} 
                  scale={20} 
                  blur={2} 
                  far={4} 
                />
                
                {/* 控制器 */}
                <OrbitControls 
                  enablePan={true}
                  enableZoom={true}
                  enableRotate={true}
                  minDistance={2}
                  maxDistance={20}
                />
              </Canvas>
            </div>

            <div className="viewer-hints">
              <Tag>🖱️ 左键旋转</Tag>
              <Tag>🖱️ 右键平移</Tag>
              <Tag>🖱️ 滚轮缩放</Tag>
              <Tag>👆 点击建筑查看材质</Tag>
            </div>
          </Card>
        </Col>

        {/* 右侧：信息和材质面板 */}
        <Col span={8}>
          <Tabs
            defaultActiveKey="materials"
            items={[
              {
                key: 'materials',
                label: '🎨 材质信息',
                children: (
                  <div className="materials-panel">
                    {materials.map((mat: any) => (
                      <Card
                        key={mat.id}
                        size="small"
                        className={`material-card ${selectedMaterial?.id === mat.id ? 'selected' : ''}`}
                        onClick={() => setSelectedMaterial(mat)}
                        hoverable
                      >
                        <div className="material-header">
                          <div
                            className="material-color"
                            style={{ backgroundColor: mat.properties.color }}
                          />
                          <div className="material-title">
                            <h4>{mat.name}</h4>
                            <Tag color={materialTypeColors[mat.type]}>
                              {materialTypeLabels[mat.type]}
                            </Tag>
                          </div>
                        </div>

                        <p className="material-desc">{mat.description}</p>

                        <div className="material-props">
                          <div className="prop-item">
                            <ExperimentOutlined />
                            <span>环保</span>
                            <Progress 
                              percent={mat.sustainability * 100} 
                              size="small"
                              strokeColor="#52c41a"
                            />
                          </div>
                          <div className="prop-item">
                            <SafetyOutlined />
                            <span>耐久</span>
                            <Progress 
                              percent={mat.durability * 100} 
                              size="small"
                              strokeColor="#1890ff"
                            />
                          </div>
                          <div className="prop-item">
                            <DollarOutlined />
                            <span>成本</span>
                            <Progress 
                              percent={mat.cost * 100} 
                              size="small"
                              strokeColor="#faad14"
                            />
                          </div>
                        </div>

                        <div className="material-location">
                          📍 应用部位：{mat.location}
                        </div>
                      </Card>
                    ))}
                  </div>
                )
              },
              {
                key: 'location',
                label: '📍 地点环境',
                children: (
                  <div className="location-panel">
                    <Card size="small" title="项目位置">
                      <div style={{ height: '200px', marginBottom: 16 }}>
                        <MapContainer
                          center={[locationData.coordinates.lat, locationData.coordinates.lng]}
                          zoom={15}
                          style={{ height: '100%', width: '100%' }}
                        >
                          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                          <Marker 
                            position={[
                              locationData.coordinates.lat, 
                              locationData.coordinates.lng
                            ]} 
                          />
                        </MapContainer>
                      </div>

                      <Descriptions column={1} size="small">
                        <Descriptions.Item label="地址">
                          {locationData.address}
                        </Descriptions.Item>
                        <Descriptions.Item label="气候">
                          <Tag color="blue">{locationData.climate.type}</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="年均温">
                          {locationData.climate.temperature.min}°C ~ {locationData.climate.temperature.max}°C
                        </Descriptions.Item>
                        <Descriptions.Item label="日照">
                          {locationData.sunlight.direction} / {locationData.sunlight.hours}h
                        </Descriptions.Item>
                      </Descriptions>

                      <div className="context-desc">
                        <h5>周边环境</h5>
                        <p>{locationData.context}</p>
                      </div>
                    </Card>
                  </div>
                )
              },
              {
                key: 'info',
                label: 'ℹ️ 项目信息',
                children: (
                  <Descriptions column={1} bordered>
                    <Descriptions.Item label="项目名称">
                      {project?.name}
                    </Descriptions.Item>
                    <Descriptions.Item label="建筑描述">
                      {project?.prompt}
                    </Descriptions.Item>
                    <Descriptions.Item label="风格">
                      {project?.style}
                    </Descriptions.Item>
                    <Descriptions.Item label="3D 模型">
                      <a href={project?.model3dUrl} target="_blank">
                        下载 .splat 文件
                      </a>
                    </Descriptions.Item>
                  </Descriptions>
                )
              }
            ]}
          />
        </Col>
      </Row>
    </div>
  );
};
