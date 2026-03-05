// API 接口封装
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// 通用请求函数
async function request(url: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers: {
      'Accept': 'application/json',
      ...options.headers
    }
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || '请求失败');
  }

  return response.json();
}

// 创建项目
export async function createProject(data: { name: string; description?: string }) {
  return request('/api/v1/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
}

// 上传草图
export async function uploadSketch(formData: FormData) {
  return request('/api/v1/generate', {
    method: 'POST',
    body: formData
  });
}

// 生成建筑效果图
export async function generateFromSketch(data: {
  sketch_path: string;
  prompt: string;
  style?: string;
}) {
  return request('/api/v1/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
}

// 启动 3D 重建
export async function startReconstruction(data: {
  image_url: string;
  method: string;
  quality?: string;
}) {
  return request('/api/v1/reconstruct', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
}

// 查询重建状态
export async function getReconstructionStatus(jobId: string) {
  return request(`/api/v1/reconstruct/${jobId}/status`);
}

// 分析材质
export async function analyzeMaterials(imageUrl: string) {
  return request(`/api/v1/materials/analyze?image_url=${encodeURIComponent(imageUrl)}`, {
    method: 'POST'
  });
}

// 获取材质库
export async function getMaterialLibrary() {
  return request('/api/v1/materials/library');
}

// 获取项目详情
export async function getProject(projectId: string) {
  return request(`/api/v1/projects/${projectId}`);
}

// 更新项目
export async function updateProject(projectId: string, data: any) {
  return request(`/api/v1/projects/${projectId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
}

// 列出所有项目
export async function listProjects() {
  return request('/api/v1/projects');
}
