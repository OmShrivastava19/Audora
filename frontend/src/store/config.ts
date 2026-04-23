// Runtime config store populated from backend /api/config/public
import { create } from 'zustand';

export interface RuntimeConfig {
  FIREBASE_WEB_API_KEY: string;
  OAUTH_CLIENT_ID: string;
  DEBUG: boolean;
}

interface ConfigStore {
  config: RuntimeConfig | null;
  loading: boolean;
  error: string | null;
  fetchConfig: () => Promise<void>;
}

export const useConfigStore = create<ConfigStore>((set) => ({
  config: null,
  loading: true,
  error: null,

  fetchConfig: async () => {
    set({ loading: true, error: null });
    try {
      const apiBase = '/api';
      const response = await fetch(`${apiBase}/config/public`);

      if (!response.ok) {
        throw new Error(`Failed to fetch config: ${response.statusText}`);
      }

      const config = (await response.json()) as RuntimeConfig;
      set({ config, loading: false });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      set({ error: errorMessage, loading: false });
      console.error('Failed to fetch runtime config:', errorMessage);
    }
  },
}));

/**
 * Initialize config store by fetching from backend.
 * Call this once on app startup.
 */
export async function initializeConfig(): Promise<void> {
  const store = useConfigStore.getState();
  await store.fetchConfig();
}

/**
 * Get a config value with fallback.
 */
export function getConfigValue(key: keyof RuntimeConfig, fallback: string = ''): string {
  const config = useConfigStore.getState().config;
  if (!config || !(key in config)) {
    console.warn(`Config key not found: ${key}`);
    return fallback;
  }
  const value = config[key];
  return typeof value === 'string' ? value : fallback;
}
