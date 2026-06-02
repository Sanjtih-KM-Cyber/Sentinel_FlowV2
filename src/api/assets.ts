import { apiClient } from './client';
import { Asset } from '../types';

export const getAssets = async (): Promise<Asset[]> => {
  const { data } = await apiClient.get('/assets');
  return data;
};
