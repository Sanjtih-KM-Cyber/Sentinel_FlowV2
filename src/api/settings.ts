import { apiClient } from './client';

export const getSettings = async (): Promise<any> => {
  const { data } = await apiClient.get('/settings');
  return data;
};
