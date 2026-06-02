import { apiClient } from './client';

export const getReports = async (): Promise<any[]> => {
  const { data } = await apiClient.get('/reports');
  return data;
};
