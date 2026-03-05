"""
AI 建筑可视化 Pipeline - 后端 API
技术栈: FastAPI + Python

提供三个核心接口:
1. /generate - 草图生成建筑效果图
2. /reconstruct - 效果图生成 3D Gaussian Splatting
3. /materials - 材质分析与信息提取
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import shutil
from pathlib import Path

# 导入各阶段服务
from services.sketch_to_render import SketchToRenderService
from services.image_to_3dgs import ImageTo3DGS
from services.material_analyzer import MaterialAnalyzer

app = FastAPI(
    title="AI Architecture Visualization API",
    description="AI 建筑可视化 Pipeline 后端服务",
    version="1.0.0"
)

# CORS 配置 - 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# 初始化服务
sketch_service = SketchToRenderService()
reconstruct_service = ImageTo3DGS()
material_service = MaterialAnalyzer()


# ============== 数据模型 ==============

class GenerationRequest(BaseModel):
    """图像生成请求"""
    prompt: str  # 建筑描述提示词
    style: Optional[str] = "modern"  # 风格: modern/classical/futuristic/minimalist
    architect_style: Optional[str] = None  # 参考建筑师风格
    materials_hint: Optional[List[str]] = []  # 材质提示
    environment: Optional[str] = "urban"  # 环境: urban/natural/waterside
    

class GenerationResponse(BaseModel):
    """图像生成响应"""
    job_id: str
    status: str  # pending/processing/completed/failed
    generated_images: List[dict] = []  # 生成的图片列表
    message: str


class ReconstructionRequest(BaseModel):
    """3D 重建请求"""
    image_url: str  # 建筑效果图 URL
    method: str = "luma"  # 重建方法: luma/wonder3d/local
    quality: str = "high"  # 质量: low/medium/high


class ReconstructionResponse(BaseModel):
    """3D 重建响应"""
    job_id: str
    status: str
    model_url: Optional[str] = None  # 3D 模型文件 URL
    format: str = "splat"  # splat/ply
    preview_image: Optional[str] = None


class MaterialInfo(BaseModel):
    """材质信息"""
    id: str
    name: str
    type: str  # concrete/glass/steel/wood/stone/composite
    properties: dict
    description: str
    confidence: float  # AI 识别置信度


class BuildingData(BaseModel):
    """完整建筑数据"""
    id: str
    name: str
    sketch_url: str
    render_url: str
    model_3d_url: str
    materials: List[MaterialInfo]
    location: Optional[dict] = None
    created_at: str


# ============== API 路由 ==============

@app.get("/")
async def root():
    """API 状态检查"""
    return {
        "status": "online",
        "service": "AI Architecture Visualization API",
        "version": "1.0.0",
        "endpoints": [
            "/api/v1/generate",
            "/api/v1/reconstruct",
            "/api/v1/materials",
            "/api/v1/projects"
        ]
    }


@app.post("/api/v1/generate", response_model=GenerationResponse)
async def generate_from_sketch(
    sketch: UploadFile = File(...),
    request: Optional[str] = None
):
    """
    Stage 1: 草图 → AI 建筑效果图
    
    接收用户上传的草图，调用 AI 生图服务生成建筑效果图
    支持多轮生成，返回多张备选图
    """
    try:
        # 1. 保存上传的草图
        job_id = str(uuid.uuid4())[:8]
        sketch_path = UPLOAD_DIR / f"{job_id}_sketch.jpg"
        
        with open(sketch_path, "wb") as f:
            shutil.copyfileobj(sketch.file, f)
        
        # 2. 调用生图服务
        # 解析 request 参数
        import json
        gen_request = GenerationRequest.parse_raw(request) if request else GenerationRequest(prompt="modern building")
        
        # 异步生成
        result = await sketch_service.generate(
            sketch_path=str(sketch_path),
            prompt=gen_request.prompt,
            style=gen_request.style,
            job_id=job_id
        )
        
        return GenerationResponse(
            job_id=job_id,
            status="completed" if result["success"] else "failed",
            generated_images=result.get("images", []),
            message="图像生成成功" if result["success"] else result.get("error", "生成失败")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/reconstruct", response_model=ReconstructionResponse)
async def reconstruct_3d(request: ReconstructionRequest):
    """
    Stage 2: 效果图 → 3D Gaussian Splatting
    
    基于建筑效果图生成 3D 模型
    支持 Luma AI (云端快速) 和本地训练 (高质量) 两种方案
    """
    try:
        job_id = str(uuid.uuid4())[:8]
        
        # 根据方法选择重建方案
        if request.method == "luma":
            # 使用 Luma AI API (快速但付费)
            result = await reconstruct_service.luma_reconstruct(
                image_url=request.image_url,
                job_id=job_id
            )
        elif request.method == "wonder3d":
            # 使用 Wonder3D + 本地 GS (免费但需要 GPU)
            result = await reconstruct_service.wonder3d_reconstruct(
                image_url=request.image_url,
                job_id=job_id
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的重建方法")
        
        return ReconstructionResponse(
            job_id=job_id,
            status=result["status"],
            model_url=result.get("model_url"),
            format=result.get("format", "splat"),
            preview_image=result.get("preview_image")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/reconstruct/{job_id}/status")
async def get_reconstruction_status(job_id: str):
    """查询 3D 重建任务状态"""
    status = await reconstruct_service.get_status(job_id)
    return {"job_id": job_id, **status}


@app.post("/api/v1/materials/analyze")
async def analyze_materials(image_url: str):
    """
    分析建筑效果图中的材质
    
    使用 GPT-4 Vision 或本地模型识别建筑材质
    返回材质列表和属性信息
    """
    try:
        materials = await material_service.analyze(image_url)
        return {
            "materials": materials,
            "total": len(materials)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/materials/library")
async def get_material_library():
    """获取材质库 (用于前端展示材质选项)"""
    materials = material_service.get_library()
    return {"materials": materials}


# ============== 项目管理 ==============

PROJECTS_DB = {}  # 简化的内存存储，生产环境应使用数据库

@app.post("/api/v1/projects")
async def create_project(
    name: str,
    sketch: UploadFile = File(...)
):
    """创建新项目"""
    project_id = str(uuid.uuid4())[:8]
    
    # 保存草图
    sketch_path = UPLOAD_DIR / f"{project_id}_sketch.jpg"
    with open(sketch_path, "wb") as f:
        shutil.copyfileobj(sketch.file, f)
    
    project = {
        "id": project_id,
        "name": name,
        "sketch_url": f"/uploads/{project_id}_sketch.jpg",
        "status": "created",  # created/generating/rendering/completed
        "render_url": None,
        "model_3d_url": None,
        "materials": [],
        "created_at": "2026-03-05T15:00:00Z"
    }
    PROJECTS_DB[project_id] = project
    
    return project


@app.get("/api/v1/projects/{project_id}")
async def get_project(project_id: str):
    """获取项目详情"""
    if project_id not in PROJECTS_DB:
        raise HTTPException(status_code=404, detail="项目不存在")
    return PROJECTS_DB[project_id]


@app.get("/api/v1/projects")
async def list_projects():
    """列出所有项目"""
    return {"projects": list(PROJECTS_DB.values())}


@app.put("/api/v1/projects/{project_id}")
async def update_project(project_id: str, data: dict):
    """更新项目数据 (如关联生成的渲染图和 3D 模型)"""
    if project_id not in PROJECTS_DB:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    PROJECTS_DB[project_id].update(data)
    return PROJECTS_DB[project_id]


# ============== 静态文件服务 ==============

@app.get("/uploads/{filename}")
async def serve_upload(filename: str):
    """提供上传文件访问"""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path)


@app.get("/outputs/{filename}")
async def serve_output(filename: str):
    """提供生成的输出文件访问"""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path)


# ============== 启动 ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
