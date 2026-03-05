import { create } from 'zustand';

interface Project {
  id: string;
  name: string;
  sketchUrl?: string;
  renderUrl?: string;
  model3dUrl?: string;
  generatedImages?: any[];
  materials?: any[];
  prompt?: string;
  style?: string;
}

interface ProjectState {
  project: Project | null;
  setProject: (project: Project | null) => void;
  updateProject: (data: Partial<Project>) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  project: null,
  
  setProject: (project) => set({ project }),
  
  updateProject: (data) => set((state) => ({
    project: state.project ? { ...state.project, ...data } : null
  }))
}));
