import { apiClient } from './client';

export interface DashboardStats {
  activeProjects: number;
  assetsDiscovered: number;
  verifiedFindings: number;
  recentScans: Array<{
    id: string;
    target: string;
    time: string;
    status: string;
  }>;
  recentReports: Array<{
    id: string;
    title: string;
    date: string;
  }>;
}

export const getDashboardStats = async (): Promise<DashboardStats> => {
  const { data } = await apiClient.get('/dashboard/stats');
  return data;
};
