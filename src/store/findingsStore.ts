import { create } from 'zustand';

interface FindingsState {
  showVerifiedOnly: boolean;
  setShowVerifiedOnly: (val: boolean) => void;
  selectedFindingId: string | null;
  setSelectedFindingId: (id: string | null) => void;
}

export const useFindingsStore = create<FindingsState>((set) => ({
  showVerifiedOnly: true,
  setShowVerifiedOnly: (val) => set({ showVerifiedOnly: val }),
  selectedFindingId: null,
  setSelectedFindingId: (id) => set({ selectedFindingId: id }),
}));
