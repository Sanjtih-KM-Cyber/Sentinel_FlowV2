import { apiClient } from './client';

export interface Scan {
  id: string;
  target: string;
  status: string;
  type: string;
  progress: number;
  workers: number;
  time: string;
}

export const getScans = async (): Promise<Scan[]> => {
  const { data } = await apiClient.get('/scans');
  return data;
};
