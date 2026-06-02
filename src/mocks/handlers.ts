import { http, HttpResponse } from 'msw';
import { mockDashboardStats } from './fixtures/dashboard';
import { mockFindings } from './fixtures/findings';
import { mockAssets } from './fixtures/assets';
import { mockSettings } from './fixtures/settings';
import { mockScans } from './fixtures/scans';

let currentOrg = {
  id: '1',
  name: 'Test Org',
  workspace_type: 'SOLO'
};

export const handlers = [
  http.get('/api/v1/dashboard/stats', () => {
    return HttpResponse.json(mockDashboardStats);
  }),
  
  http.get('/api/v1/findings', () => {
    return HttpResponse.json(mockFindings);
  }),
  
  http.get('/api/v1/assets', () => {
    return HttpResponse.json(mockAssets);
  }),

  http.get('/api/v1/settings', () => {
    return HttpResponse.json(mockSettings);
  }),

  http.get('/api/v1/scans', () => {
    return HttpResponse.json(mockScans);
  }),
  
  http.get('/api/v1/reports', () => {
    return HttpResponse.json([]);
  }),

  http.get('/api/v1/projects', () => {
    return HttpResponse.json([
      { id: '1', name: 'Client A Website', description: 'Public marketing website security assessment.', assets: 15, findings: 3 },
      { id: '2', name: 'Client B SaaS', description: 'Internal dashboard and API pentest.', assets: 8, findings: 12 },
    ]);
  }),

  http.get('/api/v1/organizations/current', () => {
    return HttpResponse.json(currentOrg);
  }),
  
  http.patch('/api/v1/organizations/current', async ({ request }) => {
    const data = await request.json() as { workspace_type: string };
    currentOrg = { ...currentOrg, workspace_type: data.workspace_type };
    return HttpResponse.json(currentOrg);
  }),
];
