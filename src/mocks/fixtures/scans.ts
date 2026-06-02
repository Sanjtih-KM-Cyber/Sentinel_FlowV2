export const mockScans = [
  {
    id: 's-1',
    target: 'api.example.com',
    status: 'RUNNING',
    type: 'Full Active Scan',
    time: '45m elapsed',
    workers: 12,
    progress: 65,
  },
  {
    id: 's-2',
    target: 'auth.example.com',
    status: 'SCHEDULED',
    type: 'Weekly Passive',
    time: 'Starts in 2h',
    workers: 0,
    progress: 0,
  },
  {
    id: 's-3',
    target: 'staging-internal',
    status: 'COMPLETED',
    type: 'Targeted Discovery',
    time: 'Completed 1d ago',
    workers: 0,
    progress: 100,
  }
];
