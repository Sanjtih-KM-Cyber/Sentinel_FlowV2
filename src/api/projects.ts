import { apiClient } from './client';

export interface Project {
  id: string;
  name: string;
  description: string;
  is_archived: boolean;
  created_at: string;
  stats?: {
    assets: number;
    findings: number;
  };
}

export const getProjects = async (): Promise<Project[]> => {
  const { data } = await apiClient.get('/projects');
  return data;
};
