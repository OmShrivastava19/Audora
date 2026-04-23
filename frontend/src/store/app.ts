import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Provider, Language, GenerationResult } from '@/types';

interface AppStore {
  // Preferences
  provider: Provider;
  language: Language;
  enableTts: boolean;
  setProvider: (p: Provider) => void;
  setLanguage: (l: Language) => void;
  setEnableTts: (v: boolean) => void;

  // Current generation result
  currentResult: GenerationResult | null;
  setCurrentResult: (r: GenerationResult | null) => void;

  // Selected segment for transcript highlight
  selectedSegmentId: string | null;
  selectedSeekSec: number;
  setSelectedSegment: (id: string | null, sec?: number) => void;

  // Sidebar
  sidebarOpen: boolean;
  setSidebarOpen: (v: boolean) => void;
}

export const useAppStore = create<AppStore>()(
  persist(
    (set) => ({
      provider: 'groq',
      language: 'English',
      enableTts: true,
      setProvider: (provider) => set({ provider }),
      setLanguage: (language) => set({ language }),
      setEnableTts: (enableTts) => set({ enableTts }),

      currentResult: null,
      setCurrentResult: (currentResult) => set({ currentResult }),

      selectedSegmentId: null,
      selectedSeekSec: 0,
      setSelectedSegment: (id, sec = 0) =>
        set({ selectedSegmentId: id, selectedSeekSec: sec }),

      sidebarOpen: true,
      setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
    }),
    {
      name: 'audora-app',
      partialize: (state) => ({
        provider: state.provider,
        language: state.language,
        enableTts: state.enableTts,
      }),
    }
  )
);
