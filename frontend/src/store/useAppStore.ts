import { create } from 'zustand';

interface AppState {
  // Example state - can be expanded as needed
  documents: any[];
  setDocuments: (docs: any[]) => void;
}

export const useAppStore = create<AppState>((set) => ({
  documents: [],
  setDocuments: (docs) => set({ documents: docs }),
}));