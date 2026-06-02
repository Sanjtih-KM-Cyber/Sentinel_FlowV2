import { useEffect } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  LayoutDashboard, 
  Server, 
  ScanSearch, 
  ShieldAlert, 
  FileText, 
  Users, 
  Settings as SettingsIcon, 
  History,
  Sun,
  Moon,
  FolderOpen
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useThemeStore } from '../../store/themeStore';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { apiClient } from '../../api/client';

export default function Layout() {
  const { isDarkMode, toggleTheme } = useThemeStore();
  const { workspaceType, setWorkspaceType } = useWorkspaceStore();
  const queryClient = useQueryClient();

  const { data: organization } = useQuery({
    queryKey: ['currentOrganization'],
    queryFn: async () => {
      const { data } = await apiClient.get('/organizations/current');
      return data;
    },
  });

  useEffect(() => {
    if (organization?.workspace_type) {
      setWorkspaceType(organization.workspace_type);
    }
  }, [organization, setWorkspaceType]);

  const updateWorkspaceMutation = useMutation({
    mutationFn: async (newType: string) => {
      const { data } = await apiClient.patch('/organizations/current', { workspace_type: newType });
      return data;
    },
    onSuccess: (data) => {
      setWorkspaceType(data.workspace_type);
      queryClient.setQueryData(['currentOrganization'], data);
    },
  });

  const handleWorkspaceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newType = e.target.value;
    updateWorkspaceMutation.mutate(newType);
  };

  const getNavigation = () => {
    const baseNav = [
      { name: 'Dashboard', href: '/', icon: LayoutDashboard },
      { name: 'Projects', href: '/projects', icon: FolderOpen },
      { name: 'Assets', href: '/assets', icon: Server },
      { name: 'Scans', href: '/scans', icon: ScanSearch },
      { name: 'Findings', href: '/findings', icon: ShieldAlert },
      { name: 'Reports', href: '/reports', icon: FileText },
      { name: 'Settings', href: '/settings', icon: SettingsIcon },
    ];

    const extraNav = [];
    if (workspaceType !== 'SOLO') {
      extraNav.push({ name: 'Team', href: '/team', icon: Users });
    }
    if (workspaceType === 'ENTERPRISE') {
      extraNav.push({ name: 'Audit Logs', href: '/audit-logs', icon: History });
    }

    // Insert extra nav before Settings
    const settingsIndex = baseNav.findIndex(i => i.name === 'Settings');
    return [
      ...baseNav.slice(0, settingsIndex),
      ...extraNav,
      ...baseNav.slice(settingsIndex)
    ];
  };

  const navigation = getNavigation();

  return (
    <div className="flex h-screen bg-brand-50 dark:bg-gray-950 transition-colors">
      <div className="w-64 bg-white dark:bg-gray-900 border-r border-brand-200 dark:border-gray-800 flex flex-col">
        <div className="h-16 flex items-center justify-between px-6 border-b border-brand-200 dark:border-gray-800">
          <div className="flex items-center">
            <ShieldAlert className="w-6 h-6 text-indigo-600 dark:text-indigo-400 mr-2" />
            <span className="font-bold text-lg text-brand-900 dark:text-gray-100 tracking-tight">EASM Core</span>
          </div>
          <button onClick={toggleTheme} className="text-brand-500 hover:text-brand-900 dark:hover:text-gray-100">
            {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.href}
              to={item.href}
              end={item.href === '/'}
              className={({ isActive }) =>
                cn(
                  'flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
                  isActive
                    ? 'bg-indigo-50 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300'
                    : 'text-brand-600 dark:text-gray-400 hover:bg-brand-100/50 dark:hover:bg-gray-800 hover:text-brand-900 dark:hover:text-gray-100'
                )
              }
            >
              <item.icon className="w-5 h-5 mr-3 shrink-0" />
              {item.name}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-brand-200 dark:border-gray-800 text-xs text-brand-500 dark:text-gray-400 flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span>Workspace: {workspaceType}</span>
            <div className={cn("w-2 h-2 rounded-full", workspaceType === 'ENTERPRISE' ? "bg-purple-500" : workspaceType === 'AGENCY' ? "bg-blue-500" : "bg-green-500")}></div>
          </div>
          <select 
            value={workspaceType}
            onChange={handleWorkspaceChange}
            disabled={updateWorkspaceMutation.isPending}
            className="w-full bg-transparent border border-brand-200 dark:border-gray-800 rounded p-1 text-xs disabled:opacity-50"
          >
            <option value="SOLO">SOLO</option>
            <option value="AGENCY">AGENCY</option>
            <option value="ENTERPRISE">ENTERPRISE</option>
          </select>
        </div>
      </div>
      
      <main className="flex-1 overflow-auto bg-brand-50 dark:bg-gray-950">
        <div className="max-w-7xl mx-auto p-6 md:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
