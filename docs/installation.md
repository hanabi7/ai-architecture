# AI 建筑可视化项目 - 安装部署指南

## 系统要求

### 最低配置
- **操作系统**: Linux (Ubuntu 20.04+), macOS, Windows (WSL2)
- **Node.js**: 18.0+
- **Python**: 3.9+
- **内存**: 8GB RAM
- **磁盘**: 10GB 可用空间

### 推荐配置 (用于本地 3D 训练)
- **GPU**: NVIDIA GPU with 8GB+ VRAM
- **CUDA**: 11.8+
- **内存**: 16GB+ RAM
- **磁盘**: 50GB+ 可用空间

---

## 快速安装

### 1. 克隆项目

```bash
git clone git@github.com:hanabi7/ai-architecture.git
cd ai-architecture
```

---

## 后端安装

### 1. 创建 Python 虚拟环境

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用你喜欢的编辑器
```

**必需配置**:
```env
# 选择 AI 生图服务: qianwen / midjourney / stability
AI_PROVIDER=qianwen

# 通义万相 API Key (国内推荐)
# 获取地址: https://dashscope.aliyun.com/
QIANWEN_API_KEY=your_qianwen_api_key_here

# Luma AI API Key (3D 重建)
# 获取地址: https://lumalabs.ai/
LUMA_API_KEY=your_luma_api_key_here

# OpenAI API Key (材质分析，可选)
# 获取地址: https://platform.openai.com/
OPENAI_API_KEY=your_openai_api_key_here
```

**可选配置** (用于本地 3D 训练):
```env
# Midjourney (通过第三方 API)
MIDJOURNEY_API_KEY=your_mj_api_key

# Stability AI
STABILITY_API_KEY=your_stability_key
```

### 4. 启动后端服务

```bash
# 开发模式 (热重载)
python app/main.py

# 或使用 uvicorn 直接启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

后端将运行在: http://localhost:8000

**验证后端**:
```bash
curl http://localhost:8000/
# 应返回: {"status": "online", ...}
```

---

## 前端安装

### 1. 安装 Node.js 依赖

```bash
cd ../frontend

# 使用 npm
npm install

# 或使用 yarn
yarn install

# 或使用 pnpm
pnpm install
```

### 2. 配置环境变量 (可选)

```bash
# 复制示例配置
cp .env.example .env.local

# 编辑配置
nano .env.local
```

**默认配置**:
```env
# API 地址
VITE_API_URL=http://localhost:8000

# 应用标题
VITE_APP_TITLE=AI 建筑可视化
```

### 3. 启动开发服务器

```bash
npm run dev
```

前端将运行在: http://localhost:3000

浏览器会自动打开，或手动访问上述地址。

---

## 生产部署

### 前端构建

```bash
cd frontend
npm run build
```

构建输出位于 `frontend/dist/` 目录。

### 使用 Nginx 部署 (推荐)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/ai-architecture/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }

    # 上传文件代理
    location /uploads/ {
        proxy_pass http://localhost:8000/uploads/;
    }

    # 输出文件代理
    location /outputs/ {
        proxy_pass http://localhost:8000/outputs/;
    }
}
```

### Docker 部署 (可选)

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - QIANWEN_API_KEY=${QIANWEN_API_KEY}
      - LUMA_API_KEY=${LUMA_API_KEY}
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/outputs:/app/outputs
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
```

运行:
```bash
docker-compose up -d
```

---

## 常见问题

### 1. 后端启动失败

**问题**: `ModuleNotFoundError: No module named 'fastapi'`

**解决**:
```bash
# 确保激活虚拟环境
source backend/venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt
```

### 2. 前端端口被占用

**问题**: `Error: Port 3000 is already in use`

**解决**:
```bash
# 使用其他端口
npm run dev -- --port 3001

# 或修改 vite.config.ts
server: {
  port: 3001
}
```

### 3. API 跨域错误

**问题**: `CORS error`

**解决**:
检查 `backend/app/main.py` 中的 CORS 配置:
```python
allow_origins=["http://localhost:3000", "http://localhost:3001"]
```

### 4. 类型检查错误

**问题**: TypeScript 编译错误

**解决**:
```bash
cd frontend
./node_modules/.bin/tsc --noEmit
```

根据错误提示修复类型问题。

### 5. Gaussian Splatting 渲染失败

**问题**: 3D 模型不显示

**解决**:
- 检查浏览器是否支持 WebGL2
- 确认模型文件格式为 `.splat` 或 `.ply`
- 查看浏览器控制台错误信息

---

## 开发模式

### 热重载

前后端都支持热重载:

```bash
# 终端 1 - 后端
cd backend
source venv/bin/activate
python app/main.py

# 终端 2 - 前端
cd frontend
npm run dev
```

### API 文档

后端启动后，访问自动生成的 API 文档:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 验证安装

### 1. 检查后端

```bash
curl http://localhost:8000/
```

预期响应:
```json
{
  "status": "online",
  "service": "AI Architecture Visualization API",
  "version": "1.0.0"
}
```

### 2. 检查前端

浏览器访问 http://localhost:3000

应看到:
- 页面标题: "AI 建筑可视化"
- 4步流程导航
- 草图上传区域

### 3. 端到端测试

1. 上传一张草图
2. 填写建筑描述
3. 点击"开始生成"
4. 检查后端日志是否有请求

---

## 下一步

安装完成后，参考 [项目文档](./docs/) 了解:
- [技术架构](./docs/pipeline-architecture.md)
- [实施路线](./docs/project-roadmap.md)
- [API 使用说明](./docs/api-guide.md)

---

## 获取帮助

如有问题:
1. 查看 [GitHub Issues](https://github.com/hanabi7/ai-architecture/issues)
2. 提交新的 Issue
3. 联系项目维护者

---

**安装完成！** 🎉
