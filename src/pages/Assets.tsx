import { Server, Globe, Hash, Zap, Code2, Network } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { getAssets } from '../api/assets';

export default function Assets() {
  const { data = [], isLoading, error } = useQuery({
    queryKey: ['assets'],
    queryFn: getAssets,
  });

  const assets = Array.isArray(data) ? data : [];

  if (isLoading) {
    return <div className="p-8 text-center bg-white dark:bg-gray-900 rounded-xl border border-brand-200 dark:border-gray-800">Loading assets...</div>;
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-500 bg-white dark:bg-gray-900 rounded-xl border border-red-200 dark:border-red-900">
        <h3 className="font-semibold text-lg mb-2">Backend Unavailable or Connection Error</h3>
        <p>Failed to load assets. The server might be down or unreachable.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-brand-900 dark:text-gray-100 tracking-tight">Asset Inventory</h1>
        <button className="px-4 py-2 bg-indigo-600 dark:bg-indigo-500 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition">
          Add Asset
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        <CategoryCard title="Domains" icon={Globe} count={assets.filter(a => a.type === 'Domain').length || 0} />
        <CategoryCard title="Subdomains" icon={Network} count={assets.filter(a => a.type === 'Subdomain').length || 0} />
        <CategoryCard title="IP Addresses" icon={Hash} count={assets.filter(a => a.type === 'IP Address').length || 0} />
        <CategoryCard title="Technologies" icon={Code2} count={assets.filter(a => a.type === 'Technology').length || 0} />
        <CategoryCard title="Open Ports" icon={Zap} count={assets.filter(a => a.type === 'Open Port').length || 0} />
        <CategoryCard title="APIs" icon={Server} count={assets.filter(a => a.type === 'API Endpoint').length || 0} />
      </div>

      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-brand-200 dark:border-gray-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-200 dark:border-gray-800 bg-brand-50/50 dark:bg-gray-900/50 flex justify-between items-center">
          <h2 className="text-sm font-semibold text-brand-900 dark:text-gray-100">Discovered Assets</h2>
          <div className="flex space-x-2">
            <input 
              type="text" 
              placeholder="Search assets..." 
              className="px-3 py-1.5 border border-brand-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-brand-900 dark:text-gray-100 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" 
            />
          </div>
        </div>
        <div className="divide-y divide-brand-100 dark:divide-gray-800">
          {(!assets || assets.length === 0) ? (
            <div className="p-8 text-center text-brand-500 dark:text-gray-400">
              No assets discovered yet.
            </div>
          ) : (
            assets.map((asset) => (
              <div key={asset.id} className="px-6 py-4 flex items-center justify-between hover:bg-brand-50/50 dark:hover:bg-gray-800/50 transition-colors">
                <div className="flex items-center">
                  <div className="w-10 h-10 rounded-lg bg-indigo-50 dark:bg-indigo-900/30 flex items-center justify-center mr-4">
                    <Server className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                  </div>
                  <div>
                    <div className="font-semibold text-brand-900 dark:text-gray-100">{asset.name || asset.domain}</div>
                    <div className="text-xs text-brand-500 dark:text-gray-400">{asset.type}</div>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  {asset.tag && (
                    <span className="px-2.5 py-1 text-xs font-medium bg-brand-100 dark:bg-gray-800 text-brand-700 dark:text-gray-300 rounded-full">
                      {asset.tag}
                    </span>
                  )}
                  {asset.count !== undefined && (
                    <span className="text-sm text-brand-500 dark:text-gray-400 w-16 text-right">
                      {asset.count > 0 ? `${asset.count} items` : '-'}
                    </span>
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

function CategoryCard({ title, icon: Icon, count }: any) {
  return (
    <div className="bg-white dark:bg-gray-900 p-5 rounded-xl border border-brand-200 dark:border-gray-800 flex items-center shadow-sm">
      <div className="p-3 bg-brand-50 dark:bg-gray-800 rounded-lg mr-4">
        <Icon className="w-6 h-6 text-brand-600 dark:text-gray-400" />
      </div>
      <div>
        <p className="text-sm font-medium text-brand-500 dark:text-gray-400">{title}</p>
        <p className="text-2xl font-bold text-brand-900 dark:text-gray-100">{count}</p>
      </div>
    </div>
  );
}
