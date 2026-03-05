import React, { useState } from 'react';
import { Upload, Button, Input, Select, Form, Card, message } from 'antd';
import { InboxOutlined, UploadOutlined } from '@ant-design/icons';
import { uploadSketch, createProject } from '../api';
import type { UploadFile } from 'antd/es/upload/interface';
import './SketchUploader.css';

const { Dragger } = Upload;
const { TextArea } = Input;

interface SketchUploaderProps {
  onUploadSuccess: (project: any) => void;
}

export const SketchUploader: React.FC<SketchUploaderProps> = ({ onUploadSuccess }) => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [form] = Form.useForm();

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.error('请先选择草图文件');
      return;
    }

    const file = fileList[0];
    const values = form.getFieldsValue();

    setUploading(true);

    try {
      // 1. 创建项目
      const project = await createProject({
        name: values.projectName || '未命名项目',
        description: values.description
      });

      // 2. 上传草图
      const formData = new FormData();
      formData.append('sketch', file as any);
      formData.append('project_id', project.id);

      const result = await uploadSketch(formData);

      onUploadSuccess({
        ...project,
        sketchUrl: result.url,
        prompt: values.prompt,
        style: values.style
      });

    } catch (error) {
      message.error('上传失败: ' + error.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card title="📐 上传建筑草图" className="sketch-uploader">
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          style: 'modern'
        }}
      >
        <Form.Item
          name="projectName"
          label="项目名称"
          rules={[{ required: true, message: '请输入项目名称' }]}
        >
          <Input placeholder="例如：现代艺术博物馆" />
        </Form.Item>

        <Form.Item
          name="prompt"
          label="建筑描述"
          rules={[{ required: true, message: '请描述你的建筑' }]}
        >
          <TextArea
            rows={3}
            placeholder="描述你想要生成的建筑类型、功能、氛围等... 例如：一座现代风格的文化中心，清水混凝土外墙，大面积玻璃幕墙"
          />
        </Form.Item>

        <Form.Item
          name="style"
          label="建筑风格"
        >
          <Select
            options={[
              { value: 'modern', label: '🏢 现代主义' },
              { value: 'classical', label: '🏛️ 古典主义' },
              { value: 'futuristic', label: '🚀 未来主义' },
              { value: 'minimalist', label: '⬜ 极简主义' },
              { value: 'organic', label: '🌿 有机建筑' },
              { value: 'brutalist', label: '🧱 粗野主义' }
            ]}
          />
        </Form.Item>

        <Form.Item label="上传草图">
          <Dragger
            fileList={fileList}
            onChange={({ fileList }) => setFileList(fileList)}
            beforeUpload={() => false} // 阻止自动上传
            accept="image/*"
            maxCount={1}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽上传草图</p>
            <p className="ant-upload-hint">支持 JPG、PNG 格式，建议分辨率 1024x1024 以上</p>
          </Dragger>
        </Form.Item>

        <Button
          type="primary"
          size="large"
          icon={<UploadOutlined />}
          onClick={handleUpload}
          loading={uploading}
          block
        >
          {uploading ? '上传中...' : '开始生成'}
        </Button>
      </Form>
    </Card>
  );
};
