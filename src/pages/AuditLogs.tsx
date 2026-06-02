export default function AuditLogs() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-900 dark:text-gray-100 tracking-tight">Audit Logs</h1>
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-brand-200 dark:border-gray-800 overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-brand-500 dark:text-gray-400 bg-brand-50/50 dark:bg-gray-900/50 uppercase border-b border-brand-200 dark:border-gray-800">
            <tr>
              <th className="px-6 py-4">Timestamp</th>
              <th className="px-6 py-4">User</th>
              <th className="px-6 py-4">Action</th>
              <th className="px-6 py-4">Resource</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-brand-100 dark:divide-gray-800">
             <tr>
               <td colSpan={4} className="px-6 py-8 text-center text-brand-500 dark:text-gray-400">
                 No audit logs available for the current context.
               </td>
             </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
