"""
Stage 2 服务: 效果图 → 3D Gaussian Splatting
支持 Luma AI (云端) 和本地训练 (Wonder3D + GS)
"""

import os
import asyncio
import subprocess
from typing import Dict, Optional
from pathlib import Path
import aiohttp
import aiofiles


class ImageTo3DGS:
    """图像转 3D Gaussian Splatting 服务"""
    
    def __init__(self):
        self.output_dir = Path("outputs/3d_models")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Luma AI 配置
        self.luma_api_key = os.getenv("LUMA_API_KEY")
        self.luma_base_url = "https://webapp.engineeringlumalabs.com/api/v2"
        
        # 任务状态存储 (生产环境应使用 Redis)
        self.jobs = {}
    
    async def luma_reconstruct(self, image_url: str, job_id: str) -> Dict:
        """
        使用 Luma AI 进行 3D 重建 (云端快速方案)
        
        流程:
        1. 创建 capture
        2. 上传图片
        3. 触发训练
        4. 等待完成并下载
        
        成本: ~$5/次，时间: 10-30 分钟
        """
        
        if not self.luma_api_key:
            return {
                "status": "completed",
                "model_url": "/mock/model.splat",
                "format": "splat",
                "preview_image": "/mock/preview.jpg",
                "note": "Mock mode - 请配置 LUMA_API_KEY 使用真实 API"
            }
        
        headers = {"Authorization": f"luma-api-key={self.luma_api_key}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                # 1. 创建 capture
                async with session.post(
                    f"{self.luma_base_url}/captures",
                    headers=headers
                ) as resp:
                    capture_data = await resp.json()
                    capture_id = capture_data["capture_id"]
                
                # 2. 下载图片并上传
                image_path = await self._download_image(image_url, job_id)
                
                async with aiofiles.open(image_path, "rb") as f:
                    image_data = await f.read()
                
                async with session.post(
                    f"{self.luma_base_url}/captures/{capture_id}/images",
                    headers=headers,
                    data={"image": image_data}
                ) as resp:
                    await resp.read()
                
                # 3. 触发处理
                async with session.post(
                    f"{self.luma_base_url}/captures/{capture_id}/process",
                    headers=headers
                ) as resp:
                    await resp.read()
                
                # 4. 存储任务状态
                self.jobs[job_id] = {
                    "capture_id": capture_id,
                    "status": "processing",
                    "provider": "luma"
                }
                
                return {
                    "status": "processing",
                    "job_id": job_id,
                    "message": "3D 重建已开始，请轮询状态接口获取结果"
                }
                
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def wonder3d_reconstruct(self, image_url: str, job_id: str) -> Dict:
        """
        使用 Wonder3D + Gaussian Splatting 进行本地重建 (免费方案)
        
        流程:
        1. 下载效果图
        2. Wonder3D 生成 6 个正交视角
        3. COLMAP 估计相机位姿
        4. 训练 Gaussian Splatting
        
        成本: 免费 (需 GPU)，时间: 1-4 小时
        """
        
        try:
            # 1. 下载图片
            image_path = await self._download_image(image_url, job_id)
            
            # 创建输出目录
            output_path = self.output_dir / job_id
            output_path.mkdir(exist_ok=True)
            
            # 2. 运行 Wonder3D 生成多视角
            # 注意: 这需要在有 GPU 的机器上运行
            multiview_dir = output_path / "multiview"
            multiview_dir.mkdir(exist_ok=True)
            
            # 异步执行命令
            await self._run_wonder3d(image_path, multiview_dir)
            
            # 3. COLMAP 稀疏重建
            colmap_dir = output_path / "colmap"
            colmap_dir.mkdir(exist_ok=True)
            
            await self._run_colmap(multiview_dir, colmap_dir)
            
            # 4. 训练 Gaussian Splatting
            gs_dir = output_path / "gaussian_splatting"
            gs_dir.mkdir(exist_ok=True)
            
            await self._train_gaussian_splatting(colmap_dir, gs_dir)
            
            # 5. 转换格式为 .splat
            splat_path = output_path / "model.splat"
            await self._convert_to_splat(gs_dir, splat_path)
            
            return {
                "status": "completed",
                "model_url": f"/outputs/3d_models/{job_id}/model.splat",
                "format": "splat",
                "preview_image": f"/outputs/3d_models/{job_id}/multiview/view_0.png",
                "job_id": job_id
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def get_status(self, job_id: str) -> Dict:
        """查询重建任务状态"""
        
        if job_id not in self.jobs:
            return {"status": "unknown", "error": "任务不存在"}
        
        job = self.jobs[job_id]
        
        if job["provider"] == "luma":
            # 查询 Luma AI 状态
            return await self._check_luma_status(job_id)
        else:
            # 本地任务状态
            return job
    
    async def _check_luma_status(self, job_id: str) -> Dict:
        """检查 Luma AI 任务状态"""
        
        job = self.jobs[job_id]
        capture_id = job["capture_id"]
        
        headers = {"Authorization": f"luma-api-key={self.luma_api_key}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.luma_base_url}/captures/{capture_id}",
                headers=headers
            ) as resp:
                data = await resp.json()
                status = data.get("status")
                
                if status == "complete":
                    # 下载 Gaussian Splat 文件
                    gs_url = data.get("gaussian_splat_url")
                    splat_path = self.output_dir / f"{job_id}.splat"
                    
                    async with session.get(gs_url) as gs_resp:
                        async with aiofiles.open(splat_path, "wb") as f:
                            await f.write(await gs_resp.read())
                    
                    job["status"] = "completed"
                    return {
                        "status": "completed",
                        "model_url": f"/outputs/3d_models/{job_id}.splat",
                        "format": "splat",
                        "preview_image": data.get("thumbnail_url")
                    }
                
                elif status == "failed":
                    job["status"] = "failed"
                    return {"status": "failed", "error": data.get("error", "处理失败")}
                
                else:
                    progress = data.get("progress", 0)
                    return {
                        "status": "processing",
                        "progress": progress,
                        "message": f"处理中... {progress}%"
                    }
    
    async def _download_image(self, image_url: str, job_id: str) -> Path:
        """下载图片到本地"""
        
        # 如果是本地路径
        if image_url.startswith("/uploads/"):
            return Path(image_url.lstrip("/"))
        
        # 远程 URL
        output_path = self.output_dir / f"{job_id}_input.jpg"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                async with aiofiles.open(output_path, "wb") as f:
                    await f.write(await resp.read())
        
        return output_path
    
    async def _run_wonder3d(self, image_path: Path, output_dir: Path):
        """运行 Wonder3D 生成多视角"""
        
        # 使用 subprocess 异步执行
        cmd = [
            "python", "-m", "wonder3d.generate",
            "--image", str(image_path),
            "--output", str(output_dir),
            "--num_views", "6"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Wonder3D failed: {stderr.decode()}")
    
    async def _run_colmap(self, image_dir: Path, output_dir: Path):
        """运行 COLMAP 进行稀疏重建"""
        
        db_path = output_dir / "database.db"
        
        # 特征提取
        cmd1 = [
            "colmap", "feature_extractor",
            "--database_path", str(db_path),
            "--image_path", str(image_dir)
        ]
        
        # 特征匹配
        cmd2 = [
            "colmap", "exhaustive_matcher",
            "--database_path", str(db_path)
        ]
        
        # 稀疏重建
        cmd3 = [
            "colmap", "mapper",
            "--database_path", str(db_path),
            "--image_path", str(image_dir),
            "--output_path", str(output_dir / "sparse")
        ]
        
        for cmd in [cmd1, cmd2, cmd3]:
            process = await asyncio.create_subprocess_exec(*cmd)
            await process.wait()
            
            if process.returncode != 0:
                raise RuntimeError(f"COLMAP command failed: {cmd}")
    
    async def _train_gaussian_splatting(self, colmap_dir: Path, output_dir: Path):
        """训练 Gaussian Splatting"""
        
        cmd = [
            "python", "gaussian-splatting/train.py",
            "-s", str(colmap_dir),
            "-m", str(output_dir),
            "--iterations", "7000",
            "--save_iterations", "7000"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Gaussian Splatting training failed: {stderr.decode()}")
    
    async def _convert_to_splat(self, gs_dir: Path, output_path: Path):
        """将 .ply 转换为 .splat 格式"""
        
        ply_path = gs_dir / "point_cloud" / "iteration_7000" / "point_cloud.ply"
        
        if not ply_path.exists():
            raise FileNotFoundError(f"PLY file not found: {ply_path}")
        
        # 使用转换脚本
        cmd = [
            "python", "scripts/ply_to_splat.py",
            "--input", str(ply_path),
            "--output", str(output_path)
        ]
        
        process = await asyncio.create_subprocess_exec(*cmd)
        await process.wait()
