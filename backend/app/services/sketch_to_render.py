"""
Stage 1 服务: 草图 → AI 建筑效果图
支持多种 AI 生图 API
"""

import os
import asyncio
from typing import List, Dict, Optional
from pathlib import Path
import base64
import aiohttp


class SketchToRenderService:
    """草图转建筑效果图服务"""
    
    def __init__(self):
        self.providers = {
            "midjourney": MidjourneyProvider(),
            "qianwen": QianwenProvider(),  # 通义万相
            "stability": StabilityProvider(),
        }
        self.default_provider = os.getenv("AI_PROVIDER", "qianwen")
    
    async def generate(
        self,
        sketch_path: str,
        prompt: str,
        style: str = "modern",
        architect_style: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> Dict:
        """
        基于草图生成建筑效果图
        
        Args:
            sketch_path: 草图文件路径
            prompt: 用户描述
            style: 建筑风格
            architect_style: 参考建筑师风格
            job_id: 任务 ID
        
        Returns:
            {
                "success": bool,
                "images": [{"url": str, "prompt": str}],
                "error": str (optional)
            }
        """
        provider = self.providers.get(self.default_provider)
        
        if not provider:
            return {"success": False, "error": f"不支持的 provider: {self.default_provider}"}
        
        # 构建完整的建筑提示词
        full_prompt = self._build_prompt(prompt, style, architect_style)
        
        # 调用 Provider 生成
        result = await provider.generate(sketch_path, full_prompt)
        
        return result
    
    def _build_prompt(
        self,
        user_prompt: str,
        style: str,
        architect_style: Optional[str]
    ) -> str:
        """构建完整的建筑效果图提示词"""
        
        # 风格映射
        style_templates = {
            "modern": "modern architecture, clean lines, minimalist design",
            "classical": "classical architecture, ornate details, columns",
            "futuristic": "futuristic architecture, parametric design, flowing curves",
            "minimalist": "minimalist architecture, pure geometry, white concrete",
            "organic": "organic architecture, biomimetic design, natural forms",
            "brutalist": "brutalist architecture, raw concrete, monumental scale"
        }
        
        # 建筑师风格参考
        architect_templates = {
            "ando": "designed by Tadao Ando, poetic use of light and shadow",
            "zaha": "designed by Zaha Hadid, fluid dynamics, sweeping curves",
            "gehry": "designed by Frank Gehry, deconstructivist, sculptural forms",
            "foster": "designed by Norman Foster, high-tech architecture, sustainable",
            "koolhaas": "designed by Rem Koolhaas, innovative programming, bold forms",
            "kengo": "designed by Kengo Kuma, natural materials, harmony with nature"
        }
        
        # 基础建筑描述
        base_prompt = f"""Architectural rendering of {user_prompt},
{style_templates.get(style, style_templates['modern'])},
{architect_templates.get(architect_style, '')},
photorealistic, 8k, architectural visualization,
surrounded by landscape, professional photography,
golden hour lighting, detailed textures"""
        
        # 中文版本 (用于通义万相)
        chinese_prompt = f"""{user_prompt}建筑效果图，
{self._translate_style(style)}风格建筑，
{self._translate_architect(architect_style) if architect_style else ''}，
超写实渲染，8K画质，专业建筑摄影，
黄昏光线，精细材质纹理"""
        
        return {
            "english": base_prompt.strip(),
            "chinese": chinese_prompt.strip()
        }
    
    def _translate_style(self, style: str) -> str:
        """翻译风格到中文"""
        translations = {
            "modern": "现代主义",
            "classical": "古典主义",
            "futuristic": "未来主义",
            "minimalist": "极简主义",
            "organic": "有机建筑",
            "brutalist": "粗野主义"
        }
        return translations.get(style, "现代")
    
    def _translate_architect(self, architect: str) -> str:
        """翻译建筑师名称"""
        translations = {
            "ando": "安藤忠雄设计风格",
            "zaha": "扎哈哈迪德设计风格",
            "gehry": "弗兰克盖里设计风格",
            "foster": "诺曼福斯特设计风格",
            "koolhaas": "库哈斯设计风格",
            "kengo": "隈研吾设计风格"
        }
        return translations.get(architect, "")


class QianwenProvider:
    """通义万相 (阿里) Provider - 国内可用"""
    
    def __init__(self):
        self.api_key = os.getenv("QIANWEN_API_KEY")
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
    
    async def generate(self, sketch_path: str, prompt: dict) -> Dict:
        """使用通义万相生图"""
        
        if not self.api_key:
            # Mock 模式 - 返回示例数据用于测试
            return {
                "success": True,
                "images": [
                    {
                        "url": "/mock/render_1.jpg",
                        "prompt": prompt["chinese"],
                        "provider": "qianwen"
                    }
                ],
                "note": "Mock mode - 请配置 QIANWEN_API_KEY 使用真实 API"
            }
        
        # 读取草图并转为 base64
        with open(sketch_path, "rb") as f:
            sketch_base64 = base64.b64encode(f.read()).decode()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "wanx-v1",
            "input": {
                "prompt": prompt["chinese"],
                "negative_prompt": "low quality, blurry, distorted architecture",
                "ref_image": sketch_base64  # 参考图 (草图)
            },
            "parameters": {
                "size": "1024*1024",
                "n": 4,  # 生成 4 张
                "style": "写实摄影"
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                headers=headers,
                json=payload
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    images = result.get("output", {}).get("results", [])
                    return {
                        "success": True,
                        "images": [
                            {"url": img["url"], "prompt": prompt["chinese"], "provider": "qianwen"}
                            for img in images
                        ]
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("message", "生成失败")
                    }


class MidjourneyProvider:
    """Midjourney Provider (需通过第三方 API)"""
    
    def __init__(self):
        self.api_key = os.getenv("MIDJOURNEY_API_KEY")
        # Midjourney 没有官方 API，需使用 goapi 等第三方服务
        self.api_url = "https://api.goapi.ai/midjourney/v2/imagine"
    
    async def generate(self, sketch_path: str, prompt: dict) -> Dict:
        """使用 Midjourney 生图"""
        
        # MJ 不支持直接图生图，需结合 ControlNet 或 Blend
        # 这里使用简化版本
        
        return {
            "success": True,
            "images": [
                {
                    "url": "/mock/mj_render_1.jpg",
                    "prompt": prompt["english"],
                    "provider": "midjourney",
                    "note": "请使用 Discord 手动操作或配置第三方 API"
                }
            ]
        }


class StabilityProvider:
    """Stability AI Provider (SDXL)"""
    
    def __init__(self):
        self.api_key = os.getenv("STABILITY_API_KEY")
        self.api_url = "https://api.stability.ai/v2beta/stable-image/control/sketch"
    
    async def generate(self, sketch_path: str, prompt: dict) -> Dict:
        """使用 SDXL + ControlNet (Sketch) 生图"""
        
        if not self.api_key:
            return {
                "success": True,
                "images": [{"url": "/mock/sd_render_1.jpg", "prompt": prompt["english"], "provider": "stability"}],
                "note": "Mock mode"
            }
        
        # 读取草图
        with open(sketch_path, "rb") as f:
            image_data = f.read()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        files = {
            "image": ("sketch.png", image_data, "image/png")
        }
        
        data = {
            "prompt": prompt["english"],
            "control_strength": 0.7,  # 草图控制强度
            "output_format": "png"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                headers=headers,
                data=data
            ) as response:
                if response.status == 200:
                    # 保存生成的图片
                    image_bytes = await response.read()
                    output_path = f"outputs/generated_{os.urandom(4).hex()}.png"
                    with open(output_path, "wb") as f:
                        f.write(image_bytes)
                    
                    return {
                        "success": True,
                        "images": [{"url": f"/{output_path}", "prompt": prompt["english"], "provider": "stability"}]
                    }
                else:
                    error = await response.text()
                    return {"success": False, "error": error}
