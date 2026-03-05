"""
Stage 3 服务: 材质分析与信息提取
使用 GPT-4 Vision 或本地模型识别建筑材质
"""

import os
from typing import List, Dict
import base64
import aiohttp


class MaterialAnalyzer:
    """建筑材质分析器"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.material_library = self._init_material_library()
    
    def _init_material_library(self) -> Dict:
        """初始化材质数据库"""
        return {
            "concrete": {
                "name": "清水混凝土",
                "name_en": "Fair-faced Concrete",
                "type": "concrete",
                "properties": {
                    "roughness": 0.8,
                    "metallic": 0.0,
                    "color": "#F5F5DC",
                    "texture": "清水模板纹理"
                },
                "sustainability": 0.85,
                "durability": 0.95,
                "cost": 0.7,
                "description": "裸露的混凝土表面，展现材料本真质感，由安藤忠雄发扬光大。具有优异的耐久性和独特的光影效果。"
            },
            "glass": {
                "name": "超白玻璃幕墙",
                "name_en": "Ultra-clear Glass Curtain Wall",
                "type": "glass",
                "properties": {
                    "roughness": 0.05,
                    "metallic": 0.1,
                    "color": "#E0F6FF",
                    "texture": "低铁钢化玻璃"
                },
                "sustainability": 0.75,
                "durability": 0.8,
                "cost": 0.85,
                "description": "高透光率玻璃，最大限度引入自然光，减少人工照明能耗。现代建筑的重要标志。"
            },
            "steel": {
                "name": "耐候钢板",
                "name_en": "Corten Steel",
                "type": "steel",
                "properties": {
                    "roughness": 0.9,
                    "metallic": 0.6,
                    "color": "#8B4513",
                    "texture": "锈蚀氧化层"
                },
                "sustainability": 0.9,
                "durability": 0.9,
                "cost": 0.75,
                "description": "表面形成稳定锈蚀层，具有独特的时间质感，维护成本低，与自然环境和谐共存。"
            },
            "wood": {
                "name": "碳化木",
                "name_en": "Shou Sugi Ban",
                "type": "wood",
                "properties": {
                    "roughness": 0.7,
                    "metallic": 0.0,
                    "color": "#2F2F2F",
                    "texture": "火烧炭化纹理"
                },
                "sustainability": 0.9,
                "durability": 0.85,
                "cost": 0.8,
                "description": "日本传统工艺，表面炭化处理提升防腐防虫性能，呈现深邃的黑色质感。"
            },
            "stone": {
                "name": "天然花岗岩",
                "name_en": "Natural Granite",
                "type": "stone",
                "properties": {
                    "roughness": 0.6,
                    "metallic": 0.0,
                    "color": "#808080",
                    "texture": "天然晶体颗粒"
                },
                "sustainability": 0.8,
                "durability": 0.98,
                "cost": 0.9,
                "description": "天然石材，耐久性极佳，独特的晶体结构呈现丰富的光影变化。"
            },
            "composite": {
                "name": "碳纤维复合材料",
                "name_en": "Carbon Fiber Composite",
                "type": "composite",
                "properties": {
                    "roughness": 0.3,
                    "metallic": 0.2,
                    "color": "#1C1C1C",
                    "texture": "编织纹理"
                },
                "sustainability": 0.7,
                "durability": 0.9,
                "cost": 0.95,
                "description": "高强度轻质材料，可实现复杂曲面造型，未来建筑的前沿材料。"
            },
            "ceramic": {
                "name": "陶板幕墙",
                "name_en": "Terracotta Facade",
                "type": "composite",
                "properties": {
                    "roughness": 0.6,
                    "metallic": 0.0,
                    "color": "#D2691E",
                    "texture": "陶土烧结纹理"
                },
                "sustainability": 0.88,
                "durability": 0.85,
                "cost": 0.75,
                "description": "天然陶土烧制，色彩温暖，具有自清洁功能，通风隔热性能优异。"
            },
            "aluminum": {
                "name": "阳极氧化铝板",
                "name_en": "Anodized Aluminum",
                "type": "metal",
                "properties": {
                    "roughness": 0.2,
                    "metallic": 0.9,
                    "color": "#C0C0C0",
                    "texture": "金属拉丝"
                },
                "sustainability": 0.82,
                "durability": 0.88,
                "cost": 0.8,
                "description": "轻质高强，表面氧化层提供优异的耐腐蚀性，可定制多种颜色和质感。"
            }
        }
    
    async def analyze(self, image_url: str) -> List[Dict]:
        """
        分析建筑效果图中的材质
        
        使用 GPT-4 Vision API 识别材质
        或基于规则匹配进行识别
        """
        
        if not self.openai_api_key:
            # Mock 模式 - 返回示例材质数据
            return self._get_mock_materials()
        
        try:
            # 下载图片
            image_base64 = await self._encode_image(image_url)
            
            # 调用 GPT-4 Vision
            materials = await self._call_gpt4v(image_base64)
            
            return materials
            
        except Exception as e:
            print(f"Material analysis error: {e}")
            return self._get_mock_materials()
    
    async def _call_gpt4v(self, image_base64: str) -> List[Dict]:
        """调用 GPT-4 Vision 识别材质"""
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "system",
                    "content": """你是一个建筑材质专家。分析这张建筑效果图，识别主要的建筑材料。
                    
对每个识别出的材质，提供以下信息：
1. 材质名称（中文）
2. 材质类型（concrete/glass/steel/wood/stone/composite/metal）
3. 外观描述（颜色、纹理、光泽度）
4. 建筑部位（外墙/屋顶/窗户/结构等）
5. 置信度（0-1）

请以 JSON 格式返回结果。"""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            ) as resp:
                result = await resp.json()
                
                # 解析 GPT 返回的结果
                content = result["choices"][0]["message"]["content"]
                
                # 提取 JSON 并补充材质库信息
                materials = self._parse_material_response(content)
                
                return materials
    
    def _parse_material_response(self, content: str) -> List[Dict]:
        """解析 GPT 返回的材质信息"""
        
        import json
        import re
        
        # 尝试从文本中提取 JSON
        try:
            # 查找 JSON 代码块
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                # 直接尝试解析整个内容
                data = json.loads(content)
            
            materials = data.get("materials", [])
            
            # 补充材质库中的详细信息
            enriched_materials = []
            for mat in materials:
                mat_type = mat.get("type", "unknown")
                if mat_type in self.material_library:
                    lib_info = self.material_library[mat_type]
                    mat.update({
                        "sustainability": lib_info["sustainability"],
                        "durability": lib_info["durability"],
                        "cost": lib_info["cost"],
                        "description": lib_info["description"]
                    })
                enriched_materials.append(mat)
            
            return enriched_materials
            
        except Exception as e:
            print(f"Parse error: {e}")
            return self._get_mock_materials()
    
    async def _encode_image(self, image_url: str) -> str:
        """将图片编码为 base64"""
        
        if image_url.startswith("data:image"):
            # 已经是 base64
            return image_url.split(",")[1]
        
        if image_url.startswith("/"):
            # 本地文件
            with open(image_url.lstrip("/"), "rb") as f:
                return base64.b64encode(f.read()).decode()
        
        # 远程 URL
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                image_data = await resp.read()
                return base64.b64encode(image_data).decode()
    
    def _get_mock_materials(self) -> List[Dict]:
        """返回示例材质数据"""
        return [
            {
                "id": "mat-001",
                "name": "清水混凝土",
                "type": "concrete",
                "location": "主体墙面",
                "properties": {
                    "color": "#F5F5DC",
                    "texture": "清水模板纹理",
                    "roughness": 0.8,
                    "metallic": 0.0
                },
                "sustainability": 0.85,
                "durability": 0.95,
                "cost": 0.7,
                "description": "裸露的混凝土表面，展现材料本真质感",
                "confidence": 0.92
            },
            {
                "id": "mat-002",
                "name": "超白玻璃幕墙",
                "type": "glass",
                "location": "采光立面",
                "properties": {
                    "color": "#E0F6FF",
                    "texture": "低铁钢化玻璃",
                    "roughness": 0.05,
                    "metallic": 0.1
                },
                "sustainability": 0.75,
                "durability": 0.8,
                "cost": 0.85,
                "description": "高透光率玻璃，最大限度引入自然光",
                "confidence": 0.88
            },
            {
                "id": "mat-003",
                "name": "耐候钢板",
                "type": "steel",
                "location": "装饰构件",
                "properties": {
                    "color": "#8B4513",
                    "texture": "锈蚀氧化层",
                    "roughness": 0.9,
                    "metallic": 0.6
                },
                "sustainability": 0.9,
                "durability": 0.9,
                "cost": 0.75,
                "description": "表面形成稳定锈蚀层，具有独特的时间质感",
                "confidence": 0.85
            }
        ]
    
    def get_library(self) -> Dict:
        """获取材质库"""
        return self.material_library
    
    def get_material_by_type(self, material_type: str) -> Dict:
        """根据类型获取材质信息"""
        return self.material_library.get(material_type, {})
