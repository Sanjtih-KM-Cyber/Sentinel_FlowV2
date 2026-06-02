import { Play, Square, RotateCw, Clock, Calendar, Activity } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { cn } from '../lib/utils';
import { getScans } from '../api/scans';

export default function Scans() {
  const { data = [], isLoading, error } = useQuery({
    queryKey: ['scans'],
    queryFn: getScans,
  });

  const scans = Array.isArray(data) ? data : [];

  if (isLoading) {
    return <div className="p-8 text-center bg-white dark:bg-gray-900 rounded-xl border border-brand-200 dark:border-gray-800">Loading scans...</div>;
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-500 bg-white dark:bg-gray-900 rounded-xl border border-red-200 dark:border-red-900">
        <h3 className="font-semibold text-lg mb-2">Backend Unavailable or Connection Error</h3>
        <p>Failed to load scans. The server might be down or unreachable.</p>
      </div>
    );
  }
  
  const activeScans = scans?.filter(s => s.status === 'RUNNING') || [];
  const activeWorkers = activeScans.reduce((acc, curr) => acc + curr.workers, 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-brand-900 dark:text-gray-100 tracking-tight">Scan Orchestration</h1>
        <div className="flex space-x-3">
          <button className="px-4 py-2 border border-brand-200 dark:border-gray-700 text-brand-700 dark:text-gray-300 bg-white dark:bg-gray-800 text-sm font-medium rounded-lg hover:bg-brand-50 dark:hover:bg-gray-700 transition flex items-center">
            <Calendar className="w-4 h-4 mr-2" />
            Schedule Scan
          </button>
          <button className="px-4 py-2 bg-indigo-600 dark:bg-indigo-500 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition flex items-center">
            <Play className="w-4 h-4 mr-2" />
            New Scan
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-900 p-5 rounded-xl border border-brand-200 dark:border-gray-800 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-brand-500 dark:text-gray-400">Active Workers</p>
            <p className="text-2xl font-bold text-brand-900 dark:text-gray-100 mt-1">{activeWorkers} / 20</p>
          </div>
          <Activity className="w-8 h-8 text-green-500 dark:text-green-400 opacity-80" />
        </div>
        <div className="bg-white dark:bg-gray-900 p-5 rounded-xl border border-brand-200 dark:border-gray-800 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-brand-500 dark:text-gray-400">Queue Depth</p>
            <p className="text-2xl font-bold text-brand-900 dark:text-gray-100 mt-1">{scans?.filter(s => s.status === 'SCHEDULED').length || 0} pending</p>
          </div>
          <Clock className="w-8 h-8 text-orange-500 dark:text-orange-400 opacity-80" />
        </div>
        <div className="bg-white dark:bg-gray-900 p-5 rounded-xl border border-brand-200 dark:border-gray-800 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-brand-500 dark:text-gray-400">Resource Usage</p>
            <p className="text-2xl font-bold text-brand-900 dark:text-gray-100 mt-1">{activeWorkers > 0 ? Math.floor((activeWorkers / 20) * 100) : 0}%</p>
          </div>
          <ServerIcon className="w-8 h-8 text-blue-500 dark:text-blue-400 opacity-80" />
        </div>
      </div>

      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-brand-200 dark:border-gray-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-200 dark:border-gray-800 bg-brand-50/50 dark:bg-gray-900/50">
          <h2 className="text-sm font-semibold text-brand-900 dark:text-gray-100">Recent & Active Scans</h2>
        </div>
        <div className="divide-y divide-brand-100 dark:divide-gray-800">
          {(!scans || scans.length === 0) ? (
            <div className="p-8 text-center text-brand-500 dark:text-gray-400">
              No scans running or completed.
            </div>
          ) : (
            scans.map((scan) => (
              <div key={scan.id} className="px-6 py-5 flex items-center justify-between hover:bg-brand-50/50 dark:hover:bg-gray-800/50 transition-colors">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-1">
                    <span className="font-semibold text-brand-900 dark:text-gray-100">{scan.target}</span>
                    <span className={cn("px-2 py-0.5 text-[10px] font-bold tracking-wider rounded uppercase flex items-center", 
                      scan.status === 'RUNNING' && 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
                      scan.status === 'SCHEDULED' && 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
                      scan.status === 'FAILED' && 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
                      scan.status === 'COMPLETED' && 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'
                    )}>
                      {scan.status === 'RUNNING' && <Activity className="w-3 h-3 mr-1 animate-pulse" />}
                      {scan.status}
                    </span>
                  </div>
                  <div className="text-xs text-brand-500 dark:text-gray-400 flex items-center">
                    <span>{scan.type}</span>
                    <span className="mx-2">•</span>
                    <span>{scan.time}</span>
                    {scan.workers > 0 && (
                      <>
                        <span className="mx-2">•</span>
                        <span>{scan.workers} workers running</span>
                      </>
                    )}
                  </div>
                  {scan.status === 'RUNNING' && (
                    <div className="mt-3 w-full max-w-md bg-brand-100 dark:bg-gray-800 rounded-full h-1.5 overflow-hidden">
                      <div className="bg-blue-500 dark:bg-blue-400 h-1.5 rounded-full" style={{ width: `${scan.progress}%` }}></div>
                    </div>
                  )}
                </div>
                
                <div className="flex items-center space-x-2">
                  {scan.status === 'RUNNING' && (
                    <button className="p-2 text-brand-400 dark:text-gray-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-gray-800 rounded bg-white dark:bg-gray-900 border border-brand-200 dark:border-gray-700 transition" title="Cancel Scan">
                      <Square className="w-4 h-4" />
                    </button>
                  )}
                  {(scan.status === 'FAILED' || scan.status === 'COMPLETED') && (
                    <button className="p-2 text-brand-400 dark:text-gray-500 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-gray-800 rounded bg-white dark:bg-gray-900 border border-brand-200 dark:border-gray-700 transition" title="Retry Scan">
                      <RotateCw className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function ServerIcon(props: any) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <rect width="20" height="8" x="2" y="2" rx="2" ry="2" />
      <rect width="20" height="8" x="2" y="14" rx="2" ry="2" />
      <line x1="6" x2="6.01" y1="6" y2="6" />
      <line x1="6" x2="6.01" y1="18" y2="18" />
    </svg>
  );
}
