# AI 建筑可视化 Pipeline 技术方案

## 整体架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│  建筑草图   │ ──▶ │  AI 生图    │ ──▶ │ 3D Gaussian     │ ──▶ │  Web 可视化  │
│  (Sketch)   │     │ (Rendering) │     │ Splatting       │     │ + 材质信息   │
└─────────────┘     └─────────────┘     └─────────────────┘     └─────────────┘
      │                    │                    │                     │
      ▼                    ▼                    ▼                     ▼
   手工/平板           Midjourney/         LumaAI/              Three.js/
   绘制草图            Stable Diffusion    Gaussian Splatter    React + GS Viewer
```

## 阶段一：草图 → AI 建筑效果图

### 技术选型

| 工具 | 优势 | 适用场景 |
|------|------|----------|
| **Midjourney** | 效果精美，建筑理解强 | 快速概念设计 |
| **Stable Diffusion XL** | 可控性强，本地部署 | 精细化调整 |
| **DALL·E 3** | 语义理解好 | 复杂描述生成 |
| **通义万相/即梦** | 中文支持好，国内可用 | 国内项目 |

### 推荐 Prompt 模板

```markdown
# 建筑效果图生成 Prompt

## 基础模板
Architectural rendering of [建筑类型], [风格描述], 
designed by [著名建筑师/风格], 
[材质描述], [环境描述], 
[视角], [光线], 
photorealistic, 8k, architectural visualization, 
--ar 16:9 --s 750 --style raw

## 示例
Architectural rendering of a modern cultural center, 
minimalist style inspired by Tadao Ando, 
exposed concrete and glass facade, 
surrounded by water features and bamboo garden, 
eye-level perspective, golden hour lighting, 
photorealistic, 8k, architectural visualization

## 中文版本（通义万相/即梦）
现代文化中心建筑效果图，极简主义风格，安藤忠雄设计灵感，
清水混凝土与玻璃幕墙，水景与竹林环绕，
人视角度，黄昏金色光线，超写实渲染，8K画质
```

### 草图转效果图工作流

```python
# sketch_to_render.py
import requests
import base64
from PIL import Image
import io

class SketchToRender:
    """草图转建筑效果图"""
    
    def __init__(self, api_key, provider="midjourney"):
        self.api_key = api_key
        self.provider = provider
    
    def generate(self, sketch_path, prompt, style_preset=None):
        """
        基于草图生成建筑效果图
        
        Args:
            sketch_path: 草图文件路径
            prompt: 建筑描述
            style_preset: 风格预设（现代/古典/未来主义等）
        """
        # 读取草图
        with open(sketch_path, "rb") as f:
            sketch_base64 = base64.b64encode(f.read()).decode()
        
        # 根据 provider 调用不同 API
        if self.provider == "midjourney":
            return self._call_midjourney(sketch_base64, prompt)
        elif self.provider == "stability":
            return self._call_stability(sketch_base64, prompt)
        elif self.provider == "qianwen":
            return self._call_qianwen(sketch_base64, prompt)
    
    def _call_stability(self, sketch_base64, prompt):
        """Stable Diffusion API (支持图生图)"""
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/control/sketch",
            headers={"Authorization": f"Bearer {self.api_key}"},
            files={"image": ("sketch.png", base64.b64decode(sketch_base64))},
            data={
                "prompt": prompt,
                "control_strength": 0.7,  # 草图控制强度
                "output_format": "png"
            }
        )
        return response.content
```

## 阶段二：效果图 → 3D Gaussian Splatting

### 技术方案对比

| 方案 | 输入 | 输出 | 精度 | 速度 | 成本 |
|------|------|------|------|------|------|
| **Luma AI** | 2-200张图片 | .ply/.splat | 高 | 10-30min | $0.5-5/次 |
| **Polycam** | 视频/图片 | .ply/.splat | 中高 | 15-45min | 免费-订阅 |
| **Gaussian Splatting (本地)** | 图片集 | .ply | 高 | 1-4h | GPU成本 |
| **DUSt3R + GS** | 单张图 | 点云+GS | 中 | 5-10min | 免费 |
| **Wonder3D / Zero123** | 单张图 | 多视图+GS | 中 | 2-5min | 免费 |

### 推荐方案：单图重建 Pipeline

对于建筑效果图（单张），推荐 **Wonder3D + Gaussian Splatting** 或 **DUSt3R + GS** 方案：

```python
# image_to_3dgs.py
import torch
import numpy as np
from PIL import Image

class ImageTo3DGS:
    """单张建筑效果图转 3D Gaussian Splatting"""
    
    def __init__(self, method="wonder3d"):
        self.method = method
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    def generate_multiview(self, image_path, num_views=6):
        """
        使用 Wonder3D 生成多视角图像
        """
        # Wonder3D: 单图生成 6 个正交视角
        from wonder3d.pipeline import Wonder3DPipeline
        
        pipe = Wonder3DPipeline.from_pretrained(
            "flamehaze1115/wonder3d-v1.0",
            torch_dtype=torch.float16
        ).to(self.device)
        
        image = Image.open(image_path).convert("RGB")
        
        # 生成 6 个视角（前、后、左、右、上、下）
        multiview_images = pipe(
            image,
            num_views=num_views,
            guidance_scale=7.5,
            num_inference_steps=50
        ).images
        
        return multiview_images
    
    def reconstruct_3dgs(self, image_folder, output_path):
        """
        使用 Gaussian Splatting 训练 3D 模型
        """
        # 1. 使用 COLMAP 估计相机位姿
        # 2. 训练 Gaussian Splatting
        
        import subprocess
        
        # COLMAP 稀疏重建
        subprocess.run([
            "colmap", "feature_extractor",
            "--database_path", f"{image_folder}/database.db",
            "--image_path", image_folder
        ])
        
        subprocess.run([
            "colmap", "exhaustive_matcher",
            "--database_path", f"{image_folder}/database.db"
        ])
        
        # Gaussian Splatting 训练
        subprocess.run([
            "python", "gaussian-splatting/train.py",
            "-s", image_folder,
            "-m", output_path,
            "--iterations", "7000"
        ])
        
        return f"{output_path}/point_cloud/iteration_7000/point_cloud.ply"


class LumaAIAdapter:
    """Luma AI API 封装 (更简单但付费)"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://webapp.engineeringlumalabs.com/api/v2"
    
    def create_capture(self, image_paths):
        """上传图片创建 3D 捕获"""
        import requests
        
        # 1. 创建 capture
        response = requests.post(
            f"{self.base_url}/captures",
            headers={"Authorization": f"luma-api-key={self.api_key}"}
        )
        capture_id = response.json()["capture_id"]
        
        # 2. 上传图片
        for img_path in image_paths:
            with open(img_path, "rb") as f:
                requests.post(
                    f"{self.base_url}/captures/{capture_id}/images",
                    headers={"Authorization": f"luma-api-key={self.api_key}"},
                    files={"image": f}
                )
        
        # 3. 触发训练
        requests.post(
            f"{self.base_url}/captures/{capture_id}/process",
            headers={"Authorization": f"luma-api-key={self.api_key}"}
        )
        
        return capture_id
    
    def get_gaussian_splat(self, capture_id, output_path):
        """下载 Gaussian Splat 文件"""
        import requests
        import time
        
        # 等待处理完成
        while True:
            response = requests.get(
                f"{self.base_url}/captures/{capture_id}",
                headers={"Authorization": f"luma-api-key={self.api_key}"}
            )
            status = response.json()["status"]
            if status == "complete":
                break
            time.sleep(10)
        
        # 下载 .splat 或 .ply 文件
        gs_url = response.json()["gaussian_splat_url"]
        
        r = requests.get(gs_url)
        with open(output_path, "wb") as f:
            f.write(r.content)
        
        return output_path
```

## 阶段三：Web 可视化 + 材质信息

### 技术栈

```
Frontend: React + TypeScript + Three.js
GS Viewer: @react-three/drei (GaussianSplat) 或 @mkkellogg/gaussian-splats-3d
UI: Ant Design / Chakra UI
State: Zustand / Redux
```

### 核心组件架构

```typescript
// src/components/BuildingViewer/index.tsx
import React, { useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Environment, ContactShadows } from '@react-three/drei';
import { GaussianSplat } from './GaussianSplat';
import { MaterialPanel } from './MaterialPanel';
import { LocationInfo } from './LocationInfo';

interface BuildingData {
  id: string;
  name: string;
  gaussianSplatUrl: string;
  materials: MaterialInfo[];
  location: LocationInfo;
  description: string;
}

interface MaterialInfo {
  id: string;
  name: string;
  type: 'concrete' | 'glass' | 'steel' | 'wood' | 'stone' | 'composite';
  properties: {
    color: string;
    texture: string;
    roughness: number;
    metallic: number;
    sustainability: number; // 环保指数
    durability: number;     // 耐久性
    cost: number;           // 成本指数
  };
  description: string;
  imageUrl: string;
}

export const BuildingViewer: React.FC<{ data: BuildingData }> = ({ data }) => {
  const [selectedMaterial, setSelectedMaterial] = useState<MaterialInfo | null>(null);
  const [showWireframe, setShowWireframe] = useState(false);
  const [activeSection, setActiveSection] = useState<string | null>(null);

  return (
    <div className="building-viewer">
      {/* 3D 视图区域 */}
      <div className="viewer-3d">
        <Canvas camera={{ position: [5, 5, 5], fov: 50 }}>
          <ambientLight intensity={0.5} />
          <directionalLight position={[10, 10, 5]} intensity={1} />
          
          {/* Gaussian Splatting 模型 */}
          <GaussianSplat 
            url={data.gaussianSplatUrl}
            onSectionClick={setActiveSection}
          />
          
          {/* 环境 */}
          <Environment preset="city" />
          <ContactShadows opacity={0.4} scale={20} blur={2} far={4} />
          
          {/* 控制器 */}
          <OrbitControls 
            enablePan={true}
            enableZoom={true}
            enableRotate={true}
            minDistance={2}
            maxDistance={20}
          />
        </Canvas>
        
        {/* 视图控制栏 */}
        <div className="viewer-controls">
          <button onClick={() => setShowWireframe(!showWireframe)}>
            {showWireframe ? '实体模式' : '线框模式'}
          </button>
          <button onClick={() => setActiveSection(null)}>
            重置视角
          </button>
        </div>
      </div>
      
      {/* 材质信息面板 */}
      <MaterialPanel 
        materials={data.materials}
        selected={selectedMaterial}
        onSelect={setSelectedMaterial}
        activeSection={activeSection}
      />
      
      {/* 地点/环境信息 */}
      <LocationInfo location={data.location} />
    </div>
  );
};
```

### Gaussian Splatting 渲染组件

```typescript
// src/components/GaussianSplat/index.tsx
import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';

// 使用 gsplat 库加载 .splat 或 .ply 文件
import * as gsplat from '@mkkellogg/gaussian-splats-3d';

interface GaussianSplatProps {
  url: string;  // .splat 或 .ply 文件 URL
  onSectionClick?: (sectionId: string) => void;
  scale?: number;
  position?: [number, number, number];
}

export const GaussianSplat: React.FC<GaussianSplatProps> = ({
  url,
  onSectionClick,
  scale = 1,
  position = [0, 0, 0]
}) => {
  const viewerRef = useRef<gsplat.Viewer | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const { scene, camera, gl } = useThree();

  useEffect(() => {
    if (!containerRef.current) return;

    // 初始化 Gaussian Splatting Viewer
    const viewer = new gsplat.Viewer({
      cameraUp: [0, 1, 0],
      initialCameraPosition: [0, 0, 5],
      initialCameraLookAt: [0, 0, 0],
      rootElement: containerRef.current,
      renderer: gl,
      camera: camera as any
    });

    viewerRef.current = viewer;

    // 加载 Gaussian Splat 文件
    viewer.addSplatScene(url, {
      showProgressBar: true,
      progressiveLoad: true
    }).then(() => {
      console.log('Gaussian Splat loaded successfully');
    });

    return () => {
      viewer.dispose();
    };
  }, [url, gl, camera]);

  // 点击检测（简化版）
  const handleClick = (event: THREE.Event) => {
    // 实现射线检测，识别点击的建筑部位
    // 根据部位 ID 触发 onSectionClick
  };

  return (
    <group position={position} scale={scale}>
      <div 
        ref={containerRef} 
        style={{ width: '100%', height: '100%' }}
        onClick={handleClick}
      />
    </group>
  );
};

// 备用方案：使用 Three.js 原生加载 .splat
export const GaussianSplatNative: React.FC<GaussianSplatProps> = ({
  url,
  scale = 1,
  position = [0, 0, 0]
}) => {
  const meshRef = useRef<THREE.Mesh>(null);

  useEffect(() => {
    // 加载 .splat 文件并解析为点云
    fetch(url)
      .then(res => res.arrayBuffer())
      .then(buffer => {
        // 解析 splat 格式
        const splatData = parseSplatFile(buffer);
        // 创建点云几何体
        const geometry = createSplatGeometry(splatData);
        if (meshRef.current) {
          meshRef.current.geometry = geometry;
        }
      });
  }, [url]);

  return (
    <mesh ref={meshRef} position={position} scale={scale}>
      <bufferGeometry />
      <shaderMaterial
        vertexShader={splatVertexShader}
        fragmentShader={splatFragmentShader}
        transparent
        depthWrite={false}
        blending={THREE.NormalBlending}
      />
    </mesh>
  );
};
```

### 材质信息面板组件

```typescript
// src/components/MaterialPanel/index.tsx
import React from 'react';
import { Card, Tag, Progress, Tooltip } from 'antd';
import { 
  ExperimentOutlined, 
  SafetyOutlined, 
  DollarOutlined,
  EnvironmentOutlined 
} from '@ant-design/icons';

interface MaterialInfo {
  id: string;
  name: string;
  type: string;
  properties: {
    color: string;
    texture: string;
    roughness: number;
    metallic: number;
    sustainability: number;
    durability: number;
    cost: number;
  };
  description: string;
  imageUrl: string;
}

interface MaterialPanelProps {
  materials: MaterialInfo[];
  selected: MaterialInfo | null;
  onSelect: (material: MaterialInfo) => void;
  activeSection: string | null;
}

const materialTypeMap: Record<string, { label: string; color: string; icon: string }> = {
  concrete: { label: '混凝土', color: '#8B8680', icon: '🏗️' },
  glass: { label: '玻璃', color: '#87CEEB', icon: '🪟' },
  steel: { label: '钢材', color: '#4682B4', icon: '🔩' },
  wood: { label: '木材', color: '#DEB887', icon: '🪵' },
  stone: { label: '石材', color: '#808080', icon: '🪨' },
  composite: { label: '复合材料', color: '#9370DB', icon: '🔧' }
};

export const MaterialPanel: React.FC<MaterialPanelProps> = ({
  materials,
  selected,
  onSelect,
  activeSection
}) => {
  return (
    <div className="material-panel">
      <h3>🏗️ 建筑材质信息</h3>
      
      {/* 材质列表 */}
      <div className="material-list">
        {materials.map(material => (
          <Card
            key={material.id}
            className={`material-card ${selected?.id === material.id ? 'selected' : ''}`}
            onClick={() => onSelect(material)}
            hoverable
            cover={<img alt={material.name} src={material.imageUrl} />}
          >
            <div className="material-header">
              <span className="material-icon">
                {materialTypeMap[material.type]?.icon || '📦'}
              </span>
              <h4>{material.name}</h4>
              <Tag color={materialTypeMap[material.type]?.color || 'default'}>
                {materialTypeMap[material.type]?.label || material.type}
              </Tag>
            </div>
            
            <p className="material-desc">{material.description}</p>
            
            {/* 属性指标 */}
            <div className="material-properties">
              <Tooltip title="环保指数">
                <div className="property-item">
                  <EnvironmentOutlined />
                  <Progress 
                    percent={material.properties.sustainability * 100} 
                    size="small"
                    strokeColor="#52c41a"
                  />
                </div>
              </Tooltip>
              
              <Tooltip title="耐久性">
                <div className="property-item">
                  <SafetyOutlined />
                  <Progress 
                    percent={material.properties.durability * 100} 
                    size="small"
                    strokeColor="#1890ff"
                  />
                </div>
              </Tooltip>
              
              <Tooltip title="成本指数">
                <div className="property-item">
                  <DollarOutlined />
                  <Progress 
                    percent={material.properties.cost * 100} 
                    size="small"
                    strokeColor="#faad14"
                  />
                </div>
              </Tooltip>
            </div>
          </Card>
        ))}
      </div>
      
      {/* 选中材质详情 */}
      {selected && (
        <div className="material-detail">
          <h4>🔍 材质详情</h4>
          <div className="detail-grid">
            <div className="detail-item">
              <label>颜色</label>
              <div 
                className="color-sample" 
                style={{ backgroundColor: selected.properties.color }}
              />
            </div>
            <div className="detail-item">
              <label>粗糙度</label>
              <span>{(selected.properties.roughness * 100).toFixed(0)}%</span>
            </div>
            <div className="detail-item">
              <label>金属度</label>
              <span>{(selected.properties.metallic * 100).toFixed(0)}%</span>
            </div>
            <div className="detail-item">
              <label>纹理</label>
              <span>{selected.properties.texture}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
```

### 地点与环境信息组件

```typescript
// src/components/LocationInfo/index.tsx
import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Card, Descriptions, Tag } from 'antd';
import { 
  EnvironmentOutlined, 
  CloudOutlined, 
  SunOutlined,
  CompassOutlined 
} from '@ant-design/icons';

interface LocationInfo {
  name: string;
  address: string;
  coordinates: { lat: number; lng: number };
  climate: {
    type: string;        // 气候类型
    temperature: { min: number; max: number }; // 年均温
    humidity: number;    // 湿度
    precipitation: number; // 降水量
  };
  sunlight: {
    direction: string;   // 主要日照方向
    hours: number;       // 日均日照时长
  };
  context: string;       // 周边环境描述
}

export const LocationInfo: React.FC<{ location: LocationInfo }> = ({ location }) => {
  return (
    <Card className="location-info" title="📍 地点与环境">
      {/* 地图 */}
      <div className="location-map">
        <MapContainer 
          center={[location.coordinates.lat, location.coordinates.lng]} 
          zoom={15}
          style={{ height: '200px', width: '100%' }}
        >
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <Marker position={[location.coordinates.lat, location.coordinates.lng]}>
            <Popup>{location.name}</Popup>
          </Marker>
        </MapContainer>
      </div>
      
      {/* 地点信息 */}
      <Descriptions column={2} size="small">
        <Descriptions.Item label={<><EnvironmentOutlined /> 地址</>}>
          {location.address}
        </Descriptions.Item>
        <Descriptions.Item label={<><CompassOutlined /> 坐标</>}>
          {location.coordinates.lat}, {location.coordinates.lng}
        </Descriptions.Item>
        <Descriptions.Item label={<><CloudOutlined /> 气候</>}>
          <Tag color="blue">{location.climate.type}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label={<><SunOutlined /> 日照</>}>
          {location.sunlight.direction} / {location.sunlight.hours}h
        </Descriptions.Item>
      </Descriptions>
      
      {/* 气候详情 */}
      <div className="climate-detail">
        <h5>🌡️ 气候数据</h5>
        <div className="climate-grid">
          <div className="climate-item">
            <span className="label">年均温</span>
            <span className="value">
              {location.climate.temperature.min}°C ~ {location.climate.temperature.max}°C
            </span>
          </div>
          <div className="climate-item">
            <span className="label">湿度</span>
            <span className="value">{location.climate.humidity}%</span>
          </div>
          <div className="climate-item">
            <span className="label">年降水量</span>
            <span className="value">{location.climate.precipitation}mm</span>
          </div>
        </div>
      </div>
      
      {/* 环境描述 */}
      <div className="context-desc">
        <h5>🏘️ 周边环境</h5>
        <p>{location.context}</p>
      </div>
    </Card>
  );
};
```

## 完整数据流示例

```typescript
// src/data/sampleBuilding.ts
import { BuildingData } from '../types';

export const sampleBuilding: BuildingData = {
  id: "building-001",
  name: "现代艺术博物馆",
  gaussianSplatUrl: "/models/museum.splat",
  description: "这是一座融合现代主义与地域文化的艺术博物馆，采用清水混凝土与玻璃幕墙结合的设计理念。",
  
  materials: [
    {
      id: "mat-001",
      name: "清水混凝土",
      type: "concrete",
      properties: {
        color: "#F5F5DC",
        texture: "清水模板纹理",
        roughness: 0.8,
        metallic: 0.0,
        sustainability: 0.85,
        durability: 0.95,
        cost: 0.7
      },
      description: "裸露的混凝土表面，展现材料本真质感，由安藤忠雄发扬光大。",
      imageUrl: "/textures/concrete.jpg"
    },
    {
      id: "mat-002",
      name: "超白玻璃幕墙",
      type: "glass",
      properties: {
        color: "#E0F6FF",
        texture: "低铁钢化玻璃",
        roughness: 0.05,
        metallic: 0.1,
        sustainability: 0.75,
        durability: 0.8,
        cost: 0.85
      },
      description: "高透光率玻璃，最大限度引入自然光，减少人工照明能耗。",
      imageUrl: "/textures/glass.jpg"
    },
    {
      id: "mat-003",
      name: "耐候钢板",
      type: "steel",
      properties: {
        color: "#8B4513",
        texture: "锈蚀氧化层",
        roughness: 0.9,
        metallic: 0.6,
        sustainability: 0.9,
        durability: 0.9,
        cost: 0.75
      },
      description: "表面形成稳定锈蚀层，具有独特的时间质感，维护成本低。",
      imageUrl: "/textures/corten.jpg"
    }
  ],
  
  location: {
    name: "杭州西湖文化区",
    address: "浙江省杭州市西湖区",
    coordinates: { lat: 30.25, lng: 120.15 },
    climate: {
      type: "亚热带季风气候",
      temperature: { min: 4, max: 33 },
      humidity: 75,
      precipitation: 1450
    },
    sunlight: {
      direction: "东南向",
      hours: 6.5
    },
    context: "位于西湖风景区边缘，周边有传统江南园林和现代商业区，需要在传统与现代之间取得平衡。"
  }
};
```

## 项目文件结构

```
ai-architecture/
├── README.md
├── docs/
│   ├── architecture.md      # 系统架构文档
│   ├── api-reference.md     # API 参考
│   └── deployment.md        # 部署指南
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── generation.py    # 图像生成接口
│   │   │   ├── reconstruction.py # 3D 重建接口
│   │   │   └── materials.py     # 材质数据接口
│   │   ├── services/
│   │   │   ├── sketch_to_render.py
│   │   │   ├── image_to_3dgs.py
│   │   │   └── material_analyzer.py
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── BuildingViewer/
│   │   │   ├── GaussianSplat/
│   │   │   ├── MaterialPanel/
│   │   │   └── LocationInfo/
│   │   ├── hooks/
│   │   ├── types/
│   │   ├── utils/
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── scripts/
│   ├── setup.sh
│   └── train_gaussian.py
└── data/
    ├── prompts/           # 提示词库
    ├── samples/           # 示例数据
    └── models/            # 预训练模型
```

## 部署方案

### 方案一：云端部署（推荐）

```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - MIDJOURNEY_API_KEY=${MIDJOURNEY_API_KEY}
      - LUMA_API_KEY=${LUMA_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data/models:/app/models
      - ./data/outputs:/app/outputs
    
  # 可选：自建 Gaussian Splatting 服务
  gs-service:
    image: gaussian-splatting:latest
    runtime: nvidia
    volumes:
      - ./data/outputs:/workspace/outputs
```

### 方案二：本地部署

```bash
# 1. 安装依赖
pip install -r backend/requirements.txt
cd frontend && npm install

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 3. 启动服务
python backend/app/main.py      # 启动后端
cd frontend && npm run dev      # 启动前端
```

## 关键技术难点与解决方案

| 难点 | 解决方案 |
|------|----------|
| 单图 3D 重建精度低 | 结合 Wonder3D + 多视角优化，或使用 LumaAI |
| GS 文件体积大 | 使用压缩格式 (.splat 比 .ply 小 10x) |
| Web 端渲染性能 | 使用 WebGL2，LOD 加载，视锥剔除 |
| 材质自动识别 | 训练 CNN 分类器或调用 GPT-4 Vision API |
| 大规模场景 | 分块加载，Octree 空间索引 |

## 下一步行动

1. **MVP 阶段**：实现草图 → Midjourney → LumaAI → Web 查看器的基础流程
2. **优化阶段**：替换为开源方案（SD + Wonder3D + 本地 GS）降低成本
3. **功能扩展**：添加 BIM 数据对接、AR 预览、日照分析等功能

需要我为哪个部分提供详细的代码实现？
