# AI 建筑可视化项目

基于 AI 的建筑效果图生成与 3D 可视化系统。

## 功能

- 📐 **草图上传** - 上传建筑草图
- 🎨 **AI 生图** - 生成建筑效果图 (Midjourney/通义万相)
- 🔧 **3D 重建** - 生成 Gaussian Splatting 3D 模型
- 👁️ **Web 可视化** - 交互式 3D 展示 + 材质信息

## 项目结构

```
ai-architecture/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── main.py
│   │   └── services/
│   └── requirements.txt
├── frontend/         # React + Three.js 前端
│   ├── src/
│   └── package.json
└── docs/            # 文档
```

## 快速开始

### 1. 启动后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

python app/main.py
```

后端运行在 http://localhost:8000

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:3000

## API 说明

| 接口 | 方法 | 描述 |
|-----|------|------|
| `/api/v1/generate` | POST | 草图生成效果图 |
| `/api/v1/reconstruct` | POST | 效果图生成 3D 模型 |
| `/api/v1/materials/analyze` | POST | 分析材质 |
| `/api/v1/projects` | CRUD | 项目管理 |

## 技术栈

- **后端**: FastAPI + Python
- **前端**: React + TypeScript + Three.js + Ant Design
- **3D 渲染**: Gaussian Splatting + WebGL

## 许可证

MIT
