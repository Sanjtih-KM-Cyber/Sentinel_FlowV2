import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { FolderOpen, Target, ShieldAlert, Plus } from 'lucide-react';
import { cn } from '../lib/utils';
import { useWorkspaceStore } from '../store/workspaceStore';
import { getProjects } from '../api/projects';

export default function Projects() {
  const { workspaceType } = useWorkspaceStore();
  const { data: projectsData, isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  const projects = Array.isArray(projectsData) ? projectsData : [];

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-brand-900 dark:text-gray-100 flex items-center">
            <FolderOpen className="w-6 h-6 mr-2 text-indigo-600 dark:text-indigo-400" />
            Projects
          </h1>
          <p className="text-brand-500 dark:text-gray-400 mt-1">
            {workspaceType === 'SOLO' 
              ? 'Manage your active consulting engagements and targets.' 
              : 'Managing projects across your organization.'}
          </p>
        </div>
        <button className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors font-medium text-sm">
          <Plus className="w-4 h-4 mr-2" />
          New Project
        </button>
      </div>

      {isLoading ? (
        <div className="p-8 text-center bg-white dark:bg-gray-900 rounded-xl border border-brand-200 dark:border-gray-800">Loading projects...</div>
      ) : error ? (
        <div className="p-8 text-center text-red-500 bg-white dark:bg-gray-900 rounded-xl border border-red-200 dark:border-red-900">
          <h3 className="font-semibold text-lg mb-2">Backend Unavailable or Connection Error</h3>
          <p>Failed to load projects. The server might be down or unreachable.</p>
        </div>
      ) : projects.length === 0 ? (
        <div className="p-8 text-center text-brand-500 dark:text-gray-400 bg-white dark:bg-gray-900 rounded-xl border border-brand-200 dark:border-gray-800">
          No projects found. Create one to get started.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
          {projects.map((project: any) => (
            <div key={project.id} className="bg-white dark:bg-gray-900 border border-brand-200 dark:border-gray-800 rounded-xl p-5 hover:border-indigo-300 dark:hover:border-indigo-700 transition-colors cursor-pointer group">
              <div className="flex justify-between items-start mb-4">
                <h3 className="font-semibold text-lg text-brand-900 dark:text-gray-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">{project.name}</h3>
                {project.is_archived ? (
                  <span className="bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 text-xs px-2 py-1 rounded font-medium border border-gray-200 dark:border-gray-700">Archived</span>
                ) : (
                  <span className="bg-brand-50 dark:bg-gray-800 text-brand-600 dark:text-gray-300 text-xs px-2 py-1 rounded font-medium border border-brand-100 dark:border-gray-700">Active</span>
                )}
              </div>
              <p className="text-sm text-brand-600 dark:text-gray-400 line-clamp-2 h-10 mb-6">
                {project.description || 'No description provided.'}
              </p>
              <div className="flex flex-wrap gap-4 pt-4 border-t border-brand-100 dark:border-gray-800">
                <div className="flex items-center text-sm text-brand-600 dark:text-gray-400">
                  <Target className="w-4 h-4 mr-1 text-indigo-500" />
                  <span className="font-medium">{project.stats?.assets || 0}</span>
                  <span className="ml-1 text-xs">Assets</span>
                </div>
                <div className="flex items-center text-sm text-brand-600 dark:text-gray-400">
                  <ShieldAlert className={cn("w-4 h-4 mr-1", (project.stats?.findings || 0) > 0 ? "text-red-500" : "text-green-500")} />
                  <span className="font-medium">{project.stats?.findings || 0}</span>
                  <span className="ml-1 text-xs">{(project.stats?.findings === 1) ? 'Finding' : 'Findings'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
