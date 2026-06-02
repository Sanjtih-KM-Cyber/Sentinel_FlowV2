export const mockDashboardStats = {
  activeProjects: 4,
  assetsDiscovered: 154,
  verifiedFindings: 42,
  recentScans: [
    { id: '1', target: 'api.example.com', status: 'COMPLETED', time: '2m' },
    { id: '2', target: 'staging-internal', status: 'RUNNING', time: '1h' },
  ],
  recentReports: [
    { id: '1', title: 'Q2 Security Assessment', date: 'Oct 24, 2024' },
    { id: '2', title: 'External Pentest', date: 'Oct 15, 2024' }
  ]
};
