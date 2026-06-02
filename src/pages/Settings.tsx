import { Key, Webhook, CreditCard, Activity } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { getSettings } from '../api/settings';

export default function Settings() {
  const { data: settingsData, isLoading, error } = useQuery({
    queryKey: ['settings'],
    queryFn: getSettings,
  });

  const settings = settingsData && !Array.isArray(settingsData) ? settingsData : null;

  if (isLoading) {
    return <div className="p-8 text-center bg-white dark:bg-gray-900 rounded-xl border border-brand-200 dark:border-gray-800">Loading settings...</div>;
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-500 bg-white dark:bg-gray-900 rounded-xl border border-red-200 dark:border-red-900">
        <h3 className="font-semibold text-lg mb-2">Backend Unavailable or Connection Error</h3>
        <p>Failed to load configuration. The server might be down or unreachable.</p>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="p-8 text-center text-brand-500 dark:text-gray-400 bg-white dark:bg-gray-900 rounded-xl border border-brand-200 dark:border-gray-800">
        No settings available.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-900 dark:text-gray-100 tracking-tight">Organization Settings</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-brand-200 dark:border-gray-800">
          <div className="px-6 py-4 border-b border-brand-200 dark:border-gray-800 flex items-center">
            <CreditCard className="w-5 h-5 text-brand-500 dark:text-gray-400 mr-2" />
            <h2 className="font-semibold text-brand-900 dark:text-gray-100">Subscription & Billing</h2>
          </div>
          <div className="p-6">
            <div className="flex justify-between items-end mb-6">
              <div>
                <p className="text-sm font-medium text-brand-500 dark:text-gray-400">Current Plan</p>
                <p className="text-xl font-bold text-brand-900 dark:text-gray-100">{settings.planName || 'Enterprise SaaS'}</p>
              </div>
              <button className="text-indigo-600 dark:text-indigo-400 text-sm font-medium hover:text-indigo-700 dark:hover:text-indigo-300">Manage Billing</button>
            </div>
            
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-brand-600 dark:text-gray-400">Scan Hours Usage</span>
                  <span className="text-brand-900 dark:text-gray-100 font-medium">{settings.scanHoursUsed || 0} / {settings.scanHoursLimit || 100} hrs</span>
                </div>
                <div className="w-full bg-brand-100 dark:bg-gray-800 rounded-full h-2">
                  <div className="bg-indigo-600 dark:bg-indigo-500 h-2 rounded-full" style={{ width: `${Math.min(100, Math.floor(((settings.scanHoursUsed || 0) / (settings.scanHoursLimit || 100)) * 100))}%` }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-brand-600 dark:text-gray-400">Active Assets</span>
                  <span className="text-brand-900 dark:text-gray-100 font-medium">{settings.assetsCount || 0} / {settings.assetsLimit || 500}</span>
                </div>
                <div className="w-full bg-brand-100 dark:bg-gray-800 rounded-full h-2">
                  <div className="bg-green-500 dark:bg-green-400 h-2 rounded-full" style={{ width: `${Math.min(100, Math.floor(((settings.assetsCount || 0) / (settings.assetsLimit || 500)) * 100))}%` }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl border border-brand-200 dark:border-gray-800">
          <div className="px-6 py-4 border-b border-brand-200 dark:border-gray-800 flex items-center">
            <Key className="w-5 h-5 text-brand-500 dark:text-gray-400 mr-2" />
            <h2 className="font-semibold text-brand-900 dark:text-gray-100">API Keys</h2>
          </div>
          <div className="p-6">
            <p className="text-sm text-brand-500 dark:text-gray-400 mb-4">Manage API keys to integrate Enterprise EASM with your CI/CD pipelines and external tools.</p>
            <button className="px-4 py-2 bg-brand-900 dark:bg-gray-800 text-white text-sm font-medium rounded-lg hover:bg-brand-800 dark:hover:bg-gray-700 transition">
              Generate New API Key
            </button>
            <div className="mt-4 pt-4 border-t border-brand-100 dark:border-gray-800 flex flex-col space-y-4">
              {(settings.apiKeys || []).map((apiKey: any) => (
                <div key={apiKey.id} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm text-brand-900 dark:text-gray-100">{apiKey.name}</p>
                    <p className="text-xs text-brand-500 dark:text-gray-400">Created {apiKey.createdAt}</p>
                  </div>
                  <button className="text-red-600 dark:text-red-400 text-sm font-medium hover:text-red-700 dark:hover:text-red-300">Revoke</button>
                </div>
               ))}
               {!(settings.apiKeys?.length) && (
                  <p className="text-xs text-brand-500 dark:text-gray-400 italic">No Active API Keys</p>
               )}
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl border border-brand-200 dark:border-gray-800">
          <div className="px-6 py-4 border-b border-brand-200 dark:border-gray-800 flex items-center">
            <Webhook className="w-5 h-5 text-brand-500 dark:text-gray-400 mr-2" />
            <h2 className="font-semibold text-brand-900 dark:text-gray-100">Webhooks</h2>
          </div>
          <div className="p-6">
            <p className="text-sm text-brand-500 dark:text-gray-400 mb-4">Send real-time alerts to Slack, Microsoft Teams, or custom HTTP endpoints upon critical discoveries.</p>
            <button className="px-4 py-2 border border-brand-200 dark:border-gray-700 text-brand-700 dark:text-gray-300 bg-white dark:bg-gray-800 text-sm font-medium rounded-lg hover:bg-brand-50 dark:hover:bg-gray-700 transition">
              Add Webhook
            </button>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl border border-brand-200 dark:border-gray-800">
          <div className="px-6 py-4 border-b border-brand-200 dark:border-gray-800 flex items-center">
            <Activity className="w-5 h-5 text-brand-500 dark:text-gray-400 mr-2" />
            <h2 className="font-semibold text-brand-900 dark:text-gray-100">Production Hardening Variables</h2>
          </div>
          <div className="p-6 space-y-4">
            <div className="flex justify-between items-center text-sm">
              <span className="text-brand-700 dark:text-gray-400">Scan Timeout Threshold</span>
              <span className="text-brand-900 dark:text-gray-100 font-mono">{settings.scanTimeout || '7200s'}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-brand-700 dark:text-gray-400">Max Worker Scalability</span>
              <span className="text-brand-900 dark:text-gray-100 font-mono">{settings.maxWorkers || '20'} Nodes</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-brand-700 dark:text-gray-400">Rate Limit Strategy</span>
              <span className="text-brand-900 dark:text-gray-100 font-mono">{settings.rateLimitStrategy || 'Adaptive Backoff'}</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
