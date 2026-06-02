import { useState } from 'react';
import { FileText, FileDown, Download, Briefcase } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { getReports } from '../api/reports';
import { getProjects } from '../api/projects';

export default function Reports() {
  const { data: reports, isLoading: reportsLoading, error } = useQuery({
    queryKey: ['reports'],
    queryFn: getReports,
  });

  const { data: projectsData, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  const projects = Array.isArray(projectsData) ? projectsData : [];
  const [selectedProject, setSelectedProject] = useState('');

  if (reportsLoading || projectsLoading) {
    return <div className="p-8 text-center bg-white dark:bg-gray-900 rounded-xl border border-brand-200 dark:border-gray-800">Loading reports...</div>;
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-500 bg-white dark:bg-gray-900 rounded-xl border border-red-200 dark:border-red-900">
        <h3 className="font-semibold text-lg mb-2">Backend Unavailable or Connection Error</h3>
        <p>Failed to load reports. The server might be down or unreachable.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-brand-900 dark:text-gray-100 tracking-tight">Reports & Exports</h1>
        <div className="flex items-center space-x-2 bg-white dark:bg-gray-900 border border-brand-200 dark:border-gray-800 rounded-lg p-1 w-full sm:w-auto">
          <Briefcase className="w-4 h-4 ml-2 text-brand-500" />
          <select 
            className="bg-transparent text-sm border-none focus:ring-0 text-brand-900 dark:text-gray-100 w-full outline-none py-1.5 px-2"
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
          >
            <option value="">Select a project to report on</option>
            {projects.map((p: any) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-brand-200 dark:border-gray-800 p-6 flex flex-col">
          <div className="flex items-center mb-4">
            <div className="p-3 bg-indigo-50 dark:bg-indigo-900/40 rounded-lg mr-4 text-indigo-600 dark:text-indigo-400">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-brand-900 dark:text-gray-100">Executive Report</h2>
              <p className="text-sm text-brand-500 dark:text-gray-400">For internal leadership.</p>
            </div>
          </div>
          <div className="flex-1 text-sm text-brand-600 dark:text-gray-400 mb-6">
            Includes overall risk score, critical high-level findings, and remediation progress over time. Stripped of technical payload evidence.
          </div>
          <div className="mt-auto">
            <button 
              disabled={!selectedProject}
              className="w-full flex justify-center items-center px-4 py-2 bg-brand-900 dark:bg-gray-800 text-white rounded-lg text-sm font-medium hover:bg-brand-800 dark:hover:bg-gray-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FileDown className="w-4 h-4 mr-2" /> Download PDF
            </button>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl border border-brand-200 dark:border-gray-800 p-6 flex flex-col">
          <div className="flex items-center mb-4">
            <div className="p-3 bg-blue-50 dark:bg-blue-900/40 rounded-lg mr-4 text-blue-600 dark:text-blue-400">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-brand-900 dark:text-gray-100">Technical Report</h2>
              <p className="text-sm text-brand-500 dark:text-gray-400">For engineering teams.</p>
            </div>
          </div>
          <div className="flex-1 text-sm text-brand-600 dark:text-gray-400 mb-6">
            Complete trace logs, payload vectors, and remediation steps grouped by CVSS severity and target asset.
          </div>
          <div className="mt-auto flex space-x-2">
            <button 
              disabled={!selectedProject}
              className="flex-1 flex justify-center items-center px-4 py-2 border border-brand-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-brand-700 dark:text-gray-300 rounded-lg text-sm font-medium hover:bg-brand-50 dark:hover:bg-gray-800 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Download className="w-4 h-4 mr-2" /> Export CSV
            </button>
            <button 
              disabled={!selectedProject}
              className="flex-1 flex justify-center items-center px-4 py-2 bg-brand-900 dark:bg-gray-800 text-white rounded-lg text-sm font-medium hover:bg-brand-800 dark:hover:bg-gray-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FileDown className="w-4 h-4 mr-2" /> PDF
            </button>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl border border-indigo-200 dark:border-indigo-900/50 p-6 flex flex-col shadow-sm">
          <div className="flex items-center mb-4">
            <div className="p-3 bg-fuchsia-50 dark:bg-fuchsia-900/40 rounded-lg mr-4 text-fuchsia-600 dark:text-fuchsia-400">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-brand-900 dark:text-gray-100">Client PDF Export</h2>
              <p className="text-sm text-brand-500 dark:text-gray-400">Client facing deliverables.</p>
            </div>
          </div>
          <div className="flex-1 text-sm text-brand-600 dark:text-gray-400 mb-6">
            Consultant-ready export. Cleanly branded, non-intimidating summaries for the final client debriefing meeting.
          </div>
          <div className="mt-auto">
            <button 
              disabled={!selectedProject}
              className="w-full flex justify-center items-center px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FileDown className="w-4 h-4 mr-2" /> Generate Client Report
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
