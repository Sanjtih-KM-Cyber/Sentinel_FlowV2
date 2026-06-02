import { create } from 'zustand';

export type WorkspaceType = 'SOLO' | 'AGENCY' | 'ENTERPRISE';

interface WorkspaceState {
  workspaceType: WorkspaceType;
  setWorkspaceType: (type: WorkspaceType) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  workspaceType: 'SOLO', // Default to SOLO
  setWorkspaceType: (type) => set({ workspaceType: type }),
}));
