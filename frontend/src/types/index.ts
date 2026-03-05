// TypeScript 类型定义

// 项目类型
export interface Project {
  id: string;
  name: string;
  description?: string;
  sketchUrl?: string;
  renderUrl?: string;
  model3dUrl?: string;
  generatedImages?: GeneratedImage[];
  materials?: Material[];
  prompt?: string;
  style?: string;
  status?: 'created' | 'generating' | 'rendering' | 'completed';
  createdAt?: string;
}

// 生成的图片
export interface GeneratedImage {
  url: string;
  prompt: string;
  provider: string;
}

// 材质信息
export interface Material {
  id: string;
  name: string;
  type: MaterialType;
  location: string;
  properties: MaterialProperties;
  sustainability: number;
  durability: number;
  cost: number;
  description: string;
  confidence?: number;
}

// 材质类型
export type MaterialType = 
  | 'concrete' 
  | 'glass' 
  | 'steel' 
  | 'wood' 
  | 'stone' 
  | 'composite' 
  | 'metal';

// 材质属性
export interface MaterialProperties {
  color: string;
  texture: string;
  roughness: number;
  metallic: number;
}

// 生成请求
export interface GenerationRequest {
  prompt: string;
  style?: string;
  architectStyle?: string;
  materialsHint?: string[];
  environment?: string;
}

// 生成响应
export interface GenerationResponse {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  generatedImages: GeneratedImage[];
  message: string;
}

// 重建请求
export interface ReconstructionRequest {
  imageUrl: string;
  method: 'luma' | 'wonder3d' | 'local';
  quality?: 'low' | 'medium' | 'high';
}

// 重建响应
export interface ReconstructionResponse {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  modelUrl?: string;
  format: 'splat' | 'ply';
  previewImage?: string;
  progress?: number;
  error?: string;
}

// 地点信息
export interface LocationInfo {
  name: string;
  address: string;
  coordinates: {
    lat: number;
    lng: number;
  };
  climate: {
    type: string;
    temperature: {
      min: number;
      max: number;
    };
    humidity: number;
    precipitation: number;
  };
  sunlight: {
    direction: string;
    hours: number;
  };
  context: string;
}

// Splat 数据
export interface SplatData {
  positions: number[];
  colors: number[];
  covA: number[];
  covB: number[];
  numSplats: number;
}
