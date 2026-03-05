import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { useThree } from '@react-three/fiber';

// Gaussian Splatting 着色器
const vertexShader = `
  attribute vec4 a_position;
  attribute vec4 a_color;
  attribute vec3 a_covA;
  attribute vec3 a_covB;
  
  varying vec4 v_color;
  varying vec2 v_position;
  
  uniform mat4 projectionMatrix;
  uniform mat4 modelViewMatrix;
  uniform vec2 focal;
  uniform vec2 viewport;
  
  void main() {
    vec4 center = modelViewMatrix * vec4(a_position.xyz, 1.0);
    
    // 计算协方差矩阵
    mat3 Vrk = mat3(
      a_covA.x, a_covA.y, a_covA.z,
      a_covA.y, a_covB.x, a_covB.y,
      a_covA.z, a_covB.y, a_covB.z
    );
    
    mat3 J = mat3(
      focal.x / center.z, 0.0, -(focal.x * center.x) / (center.z * center.z),
      0.0, focal.y / center.z, -(focal.y * center.y) / (center.z * center.z),
      0.0, 0.0, 0.0
    );
    
    mat3 T = J * Vrk * transpose(J);
    
    // 计算 2D 高斯参数
    float mid = (T[0][0] + T[1][1]) / 2.0;
    float radius = length(vec2((T[0][0] - T[1][1]) / 2.0, T[0][1]));
    float lambda1 = mid + radius;
    float lambda2 = mid - radius;
    
    vec2 diagonalVector = normalize(vec2(T[0][1], lambda1 - T[0][0]));
    vec2 v1 = min(sqrt(2.0 * lambda1), 1024.0) * diagonalVector;
    vec2 v2 = min(sqrt(2.0 * lambda2), 1024.0) * vec2(diagonalVector.y, -diagonalVector.x);
    
    // 顶点位置
    vec2 corner = vec2(
      gl_VertexID == 0 || gl_VertexID == 1 ? 1.0 : -1.0,
      gl_VertexID == 0 || gl_VertexID == 3 ? 1.0 : -1.0
    );
    
    vec2 pos = center.xy + corner.x * v1 + corner.y * v2;
    
    v_color = a_color;
    v_position = corner;
    
    gl_Position = projectionMatrix * vec4(pos, center.z, 1.0);
  }
`;

const fragmentShader = `
  varying vec4 v_color;
  varying vec2 v_position;
  
  void main() {
    float A = -dot(v_position, v_position);
    if (A < -4.0) discard;
    float B = exp(A) * v_color.a;
    gl_FragColor = vec4(v_color.rgb, B);
  }
`;

interface GaussianSplatMeshProps {
  url: string;
  onSectionClick?: (sectionId: string) => void;
}

export const GaussianSplatMesh: React.FC<GaussianSplatMeshProps> = ({
  url
}) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const { gl } = useThree();
  const splatDataRef = useRef<any>(null);

  useEffect(() => {
    loadSplatFile(url);
  }, [url]);

  const loadSplatFile = async (url: string) => {
    try {
      const response = await fetch(url);
      const buffer = await response.arrayBuffer();
      
      // 解析 .splat 文件
      const splatData = parseSplatBuffer(buffer);
      splatDataRef.current = splatData;
      
      // 创建几何体
      createSplatGeometry(splatData);
      
    } catch (error) {
      console.error('Failed to load splat file:', error);
    }
  };

  const parseSplatBuffer = (buffer: ArrayBuffer) => {
    const uint8 = new Uint8Array(buffer);
    const float32 = new Float32Array(buffer);
    
    // .splat 文件格式：
    // 每个 splat 32 字节
    // 位置 (3 float): 0-11 bytes
    // 缩放 (3 float): 12-23 bytes  
    // 颜色 (4 uint8): 24-27 bytes
    // 旋转 (4 uint8): 28-31 bytes
    
    const numSplats = buffer.byteLength / 32;
    
    const positions = [];
    const colors = [];
    const covA = [];
    const covB = [];
    
    for (let i = 0; i < numSplats; i++) {
      const offset = i * 32;
      
      // 位置
      const x = float32[offset / 4];
      const y = float32[offset / 4 + 1];
      const z = float32[offset / 4 + 2];
      positions.push(x, y, z);
      
      // 颜色 (uint8，需要归一化到 0-1)
      const r = uint8[offset + 24] / 255;
      const g = uint8[offset + 25] / 255;
      const b = uint8[offset + 26] / 255;
      const a = uint8[offset + 27] / 255;
      colors.push(r, g, b, a);
      
      // 简化的协方差计算 (实际应根据缩放和旋转计算)
      covA.push(0.1, 0, 0);
      covB.push(0.1, 0, 0.1);
    }
    
    return { positions, colors, covA, covB, numSplats };
  };

  const createSplatGeometry = (data: any) => {
    if (!meshRef.current) return;
    
    const geometry = new THREE.BufferGeometry();
    
    // 每个 splat 渲染为一个三角形带 (4 个顶点)
    const vertexCount = data.numSplats * 4;
    
    const positions = new Float32Array(vertexCount * 3);
    const colors = new Float32Array(vertexCount * 4);
    const covA = new Float32Array(vertexCount * 3);
    const covB = new Float32Array(vertexCount * 3);
    
    for (let i = 0; i < data.numSplats; i++) {
      const baseIdx = i * 4;
      
      for (let j = 0; j < 4; j++) {
        const idx = (baseIdx + j) * 3;
        const cidx = (baseIdx + j) * 4;
        
        // 复制位置数据
        positions[idx] = data.positions[i * 3];
        positions[idx + 1] = data.positions[i * 3 + 1];
        positions[idx + 2] = data.positions[i * 3 + 2];
        
        // 复制颜色数据
        colors[cidx] = data.colors[i * 4];
        colors[cidx + 1] = data.colors[i * 4 + 1];
        colors[cidx + 2] = data.colors[i * 4 + 2];
        colors[cidx + 3] = data.colors[i * 4 + 3];
        
        // 复制协方差
        covA[idx] = data.covA[i * 3];
        covA[idx + 1] = data.covA[i * 3 + 1];
        covA[idx + 2] = data.covA[i * 3 + 2];
        
        covB[idx] = data.covB[i * 3];
        covB[idx + 1] = data.covB[i * 3 + 1];
        covB[idx + 2] = data.covB[i * 3 + 2];
      }
    }
    
    geometry.setAttribute('a_position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('a_color', new THREE.BufferAttribute(colors, 4));
    geometry.setAttribute('a_covA', new THREE.BufferAttribute(covA, 3));
    geometry.setAttribute('a_covB', new THREE.BufferAttribute(covB, 3));
    
    meshRef.current.geometry = geometry;
  };

  return (
    <mesh ref={meshRef}>
      <shaderMaterial
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        transparent
        depthWrite={false}
        blending={THREE.NormalBlending}
        uniforms={{
          focal: { value: new THREE.Vector2(1000, 1000) },
          viewport: { value: new THREE.Vector2(gl.domElement.width, gl.domElement.height) }
        }}
      />
    </mesh>
  );
};
