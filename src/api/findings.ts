import { apiClient } from './client';
import { Finding } from '../types';

export const getFindings = async (verifiedOnly: boolean): Promise<Finding[]> => {
  const { data } = await apiClient.get('/findings', { params: { verifiedOnly } });
  return data;
};
