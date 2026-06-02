import { ShieldAlert, Server, Activity, CheckCircle2, FolderOpen, FileText } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { getDashboardStats } from '../api/dashboard';

export default function Dashboard() {
  const { data: statsData, isLoading, error } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: getDashboardStats,
  });

  const stats = statsData && !Array.isArray(statsData) ? statsData : null;

  if (isLoading) {
    return <div className="animate-pulse space-y-6">
      <div className="h-8 bg-brand-200 dark:bg-gray-800 w-48 rounded"></div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map(i => <div key={i} className="h-32 bg-brand-200 dark:bg-gray-800 rounded-xl"></div>)}
      </div>
    </div>;
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-500 bg-white dark:bg-gray-900 rounded-xl border border-red-200 dark:border-red-900">
        <h3 className="font-semibold text-lg mb-2">Backend Unavailable or Connection Error</h3>
        <p>Failed to load dashboard statistics. The server might be down or unreachable.</p>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-8 text-center text-brand-500 dark:text-gray-400 bg-white dark:bg-gray-900 rounded-xl border border-brand-200 dark:border-gray-800">
        No dashboard data available.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-brand-900 dark:text-gray-100 tracking-tight">Overview</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard icon={FolderOpen} label="Active Projects" value={stats.activeProjects || 0} color="text-indigo-600 dark:text-indigo-400" />
        <StatCard icon={Server} label="Assets Discovered" value={stats.assetsDiscovered || 0} color="text-brand-600 dark:text-brand-400" />
        <StatCard icon={CheckCircle2} label="Verified Findings" value={stats.verifiedFindings || 0} color="text-green-600 dark:text-green-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-brand-200 dark:border-gray-800 overflow-hidden">
          <div className="px-6 py-4 border-b border-brand-200 dark:border-gray-800 bg-brand-50/50 dark:bg-gray-900/50 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-brand-500 dark:text-gray-400" />
            <h2 className="text-sm font-semibold text-brand-900 dark:text-gray-100">Recent Scans</h2>
          </div>
          <div className="divide-y divide-brand-100 dark:divide-gray-800">
            {stats.recentScans && stats.recentScans.length > 0 ? (
              stats.recentScans.map((scan) => (
                <div key={scan.id} className="px-6 py-4 flex items-center justify-between hover:bg-brand-50/50 dark:hover:bg-gray-800/50 transition-colors">
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-brand-900 dark:text-gray-100">{scan.target}</span>
                    <span className="text-xs text-brand-500 dark:text-gray-400 mt-1">{scan.status}</span>
                  </div>
                  <span className="text-xs font-medium text-brand-400 dark:text-brand-300 bg-brand-100 dark:bg-gray-800 px-2 py-1 rounded-full">{scan.time} ago</span>
                </div>
              ))
            ) : (
              <div className="px-6 py-8 text-center text-brand-500 dark:text-gray-400 text-sm">
                No recent scans found.
              </div>
            )}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-brand-200 dark:border-gray-800 overflow-hidden">
          <div className="px-6 py-4 border-b border-brand-200 dark:border-gray-800 bg-brand-50/50 dark:bg-gray-900/50 flex items-center">
            <FileText className="w-5 h-5 mr-2 text-brand-500 dark:text-gray-400" />
            <h2 className="text-sm font-semibold text-brand-900 dark:text-gray-100">Recent Reports</h2>
          </div>
          <div className="divide-y divide-brand-100 dark:divide-gray-800">
            {stats.recentReports && stats.recentReports.length > 0 ? (
              stats.recentReports.map((report) => (
                <div key={report.id} className="px-6 py-4 flex items-center justify-between hover:bg-brand-50/50 dark:hover:bg-gray-800/50 transition-colors">
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-brand-900 dark:text-gray-100">{report.title}</span>
                  </div>
                  <span className="text-xs font-medium text-brand-400 dark:text-brand-300 bg-brand-100 dark:bg-gray-800 px-2 py-1 rounded-full">{report.date}</span>
                </div>
              ))
            ) : (
              <div className="px-6 py-8 text-center text-brand-500 dark:text-gray-400 text-sm">
                No recent reports found.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color = "text-brand-600 dark:text-brand-400" }: any) {
  return (
    <div className="bg-white dark:bg-gray-900 p-6 rounded-xl shadow-sm border border-brand-200 dark:border-gray-800">
      <div className="flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-medium text-brand-600 dark:text-gray-400">{label}</span>
          <Icon className={`w-5 h-5 ${color}`} />
        </div>
        <span className="text-3xl font-bold tracking-tight text-brand-900 dark:text-gray-100">{value}</span>
      </div>
    </div>
  );
}
