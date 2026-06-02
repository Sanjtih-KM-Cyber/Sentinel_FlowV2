import { apiClient } from './client';

export const getAuthSession = async (): Promise<any> => {
  const { data } = await apiClient.get('/auth/session');
  return data;
};
