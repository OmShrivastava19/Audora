import type {
  User,
  GenerationResult,
  LectureHistoryItem,
  Provider,
  Language,
} from '@/types';
import { sleep } from '@/lib/utils';
import {
  mockGenerationResult,
  mockLectureHistory,
} from './mock-data';

// ── Base API Client ──
import { getConfigValue } from '@/store/config';

// ── Base API Client ──
const API_BASE = '/api';
const DEMO_MODE = import.meta.env.MODE === 'demo' || false; // Controlled only via build/deployment

// Firebase and Google auth config will be fetched from backend
// via useConfigStore at runtime, not from env vars

type FirebaseAuthResponse = {
  localId: string;
  email: string;
  idToken: string;
  refreshToken: string;
  expiresIn: string;
};

interface ApiError {
  message: string;
  status: number;
}

interface GoogleIdentityServices {
  accounts: {
    oauth2: {
      initTokenClient: (config: {
        client_id: string;
        scope: string;
        prompt?: string;
        callback: (response: { access_token?: string; error?: string }) => void;
      }) => {
        requestAccessToken: (options?: { prompt?: string }) => void;
      };
    };
  };
}

declare global {
  interface Window {
    google?: GoogleIdentityServices;
  }
}

function getFirebaseApiKey(): string {
  const key = getConfigValue('FIREBASE_WEB_API_KEY');
  if (!key) {
    throw new Error(
      'Firebase API key is not available. ' +
      'Ensure the backend is running and /api/config/public is accessible.'
    );
  }
  return key;
}

function getGoogleClientId(): string {
  const id = getConfigValue('OAUTH_CLIENT_ID');
  if (!id) {
    throw new Error(
      'Google OAuth client ID is not available. ' +
      'Ensure the backend is running and /api/config/public is accessible.'
    );
  }
  return id;
}

async function loadScript(src: string): Promise<void> {
  if (document.querySelector(`script[src="${src}"]`)) return;

  await new Promise<void>((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
    document.head.appendChild(script);
  });
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    let message = res.statusText;
    try {
      const payload = await res.json();
      message = payload?.message || payload?.error?.message || message;
    } catch {
      // ignore parse failures and use status text
    }
    throw { message, status: res.status } satisfies ApiError;
  }
  return res.json() as Promise<T>;
}

function buildUserFromAuthResponse(data: FirebaseAuthResponse): User {
  return {
    uid: data.localId,
    email: data.email,
    plan: 'free',
    generationsUsed: 0,
    createdAt: new Date().toISOString(),
    lastLogin: new Date().toISOString(),
  };
}


class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string | null) {
    this.token = token;
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    const res = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    });
    if (!res.ok) {
      const err: ApiError = {
        message: (await res.json().catch(() => ({}))).message || res.statusText,
        status: res.status,
      };
      throw err;
    }
    return res.json();
  }

  // ── Auth ──
  async login(email: string, password: string): Promise<{ user: User; idToken: string; refreshToken: string; expiresIn: number }> {
    if (DEMO_MODE) {
      await sleep(800);
      return {
        user: {
          uid: 'demo_user_001',
          email,
          plan: 'free',
          generationsUsed: 12,
          createdAt: '2026-03-01T00:00:00Z',
          lastLogin: new Date().toISOString(),
        },
        idToken: 'demo_id_token_' + Date.now(),
        refreshToken: 'demo_refresh_token_' + Date.now(),
        expiresIn: 3600,
      };
    }

    const data = await fetchJson<FirebaseAuthResponse>(
      `https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=${getFirebaseApiKey()}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, returnSecureToken: true }),
      }
    );

    return {
      user: buildUserFromAuthResponse(data),
      idToken: data.idToken,
      refreshToken: data.refreshToken,
      expiresIn: Number(data.expiresIn),
    };
  }

  async register(email: string, password: string): Promise<{ user: User; idToken: string; refreshToken: string; expiresIn: number }> {
    if (DEMO_MODE) {
      await sleep(1000);
      return {
        user: {
          uid: 'demo_user_' + Date.now(),
          email,
          plan: 'free',
          generationsUsed: 0,
          createdAt: new Date().toISOString(),
          lastLogin: new Date().toISOString(),
        },
        idToken: 'demo_id_token_' + Date.now(),
        refreshToken: 'demo_refresh_token_' + Date.now(),
        expiresIn: 3600,
      };
    }

    const data = await fetchJson<FirebaseAuthResponse>(
      `https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=${getFirebaseApiKey()}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, returnSecureToken: true }),
      }
    );

    return {
      user: buildUserFromAuthResponse(data),
      idToken: data.idToken,
      refreshToken: data.refreshToken,
      expiresIn: Number(data.expiresIn),
    };
  }

  async loginWithGoogle(): Promise<{ user: User; idToken: string; refreshToken: string; expiresIn: number }> {
    if (DEMO_MODE) {
      await sleep(1200);
      return {
        user: {
          uid: 'demo_google_user_001',
          email: 'demo@example.com',
          plan: 'free',
          generationsUsed: 5,
          createdAt: '2026-02-15T00:00:00Z',
          lastLogin: new Date().toISOString(),
        },
        idToken: 'demo_google_token_' + Date.now(),
        refreshToken: 'demo_google_refresh_' + Date.now(),
        expiresIn: 3600,
      };
    }

    await loadScript('https://accounts.google.com/gsi/client');

    const google = window.google;
    if (!google) {
      throw new Error('Google sign-in is unavailable in this browser.');
    }

    const accessToken = await new Promise<string>((resolve, reject) => {
      const client = google.accounts.oauth2.initTokenClient({
        client_id: getGoogleClientId(),
        scope: 'openid email profile',
        prompt: 'select_account',
        callback: (response) => {
          if (response.error) {
            reject(new Error(response.error));
            return;
          }

          if (!response.access_token) {
            reject(new Error('Google sign-in did not return an access token.'));
            return;
          }

          resolve(response.access_token);
        },
      });

      client.requestAccessToken({ prompt: 'select_account' });
    });

    const data = await fetchJson<FirebaseAuthResponse>(
      `https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key=${getFirebaseApiKey()}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          postBody: `access_token=${encodeURIComponent(accessToken)}&providerId=google.com`,
          requestUri: window.location.origin,
          returnSecureToken: true,
          returnIdpCredential: true,
        }),
      }
    );

    return {
      user: buildUserFromAuthResponse(data),
      idToken: data.idToken,
      refreshToken: data.refreshToken,
      expiresIn: Number(data.expiresIn),
    };
  }

  async refreshSession(refreshToken: string): Promise<{ idToken: string; refreshToken: string; expiresIn: number }> {
    if (DEMO_MODE) {
      return {
        idToken: 'demo_id_token_' + Date.now(),
        refreshToken,
        expiresIn: 3600,
      };
    }

    const data = await fetchJson<{
      id_token: string;
      refresh_token: string;
      expires_in: string;
    }>(`https://securetoken.googleapis.com/v1/token?key=${getFirebaseApiKey()}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'refresh_token',
        refresh_token: refreshToken,
      }).toString(),
    });

    return {
      idToken: data.id_token,
      refreshToken: data.refresh_token,
      expiresIn: Number(data.expires_in),
    };
  }

  // ── Generation ──
  async generateNotes(
    _lectureFile: File,
    _syllabusFile: File | null,
    _provider: Provider,
    _language: Language,
    _apiKey: string,
    onProgress?: (stage: string, progress: number) => void,
  ): Promise<GenerationResult> {
    if (!DEMO_MODE) {
      const formData = new FormData();
      formData.append('lecture', _lectureFile);
      if (_syllabusFile) formData.append('syllabus', _syllabusFile);
      formData.append('provider', _provider);
      formData.append('language', _language);
      if (_apiKey) {
        formData.append('apiKey', _apiKey);
      }

      let response: Response;
      try {
        response = await fetch(`${this.baseUrl}/generate`, {
          method: 'POST',
          headers: this.token ? { Authorization: `Bearer ${this.token}` } : undefined,
          body: formData,
        });
      } catch {
        throw {
          message:
            `Unable to reach API server at /api/generate. ` +
            'Ensure the backend is running at http://localhost:8000',
          status: 0,
        } satisfies ApiError;
      }

      if (!response.ok) {
        throw { message: (await response.json().catch(() => ({}))).message || response.statusText, status: response.status } satisfies ApiError;
      }

      return response.json();
    }

    // Mock pipeline stages
    const stages = [
      { label: 'Processing syllabus...', progress: 15 },
      { label: 'Transcribing lecture...', progress: 40 },
      { label: 'Retrieving syllabus context...', progress: 60 },
      { label: 'Generating structured notes...', progress: 78 },
      { label: 'Computing coverage...', progress: 85 },
      { label: 'Generating study practice...', progress: 92 },
      { label: 'Generating audio notes...', progress: 96 },
      { label: 'Done!', progress: 100 },
    ];

    for (const stage of stages) {
      onProgress?.(stage.label, stage.progress);
      await sleep(600 + Math.random() * 400);
    }

    return {
      ...mockGenerationResult,
      id: 'gen_' + Date.now(),
      created_at: new Date().toISOString(),
      provider: _provider,
      lecture_filename: _lectureFile.name,
    };
  }

  // ── History ──
  async getLectureHistory(): Promise<LectureHistoryItem[]> {
    if (DEMO_MODE) {
      await sleep(500);
      return mockLectureHistory;
    }

    return fetchJson<LectureHistoryItem[]>(`${this.baseUrl}/history`, {
      headers: this.token ? { Authorization: `Bearer ${this.token}` } : undefined,
    });
  }

  async getGenerationResult(id: string): Promise<GenerationResult> {
    if (DEMO_MODE) {
      await sleep(400);
      return { ...mockGenerationResult, id };
    }

    return fetchJson<GenerationResult>(`${this.baseUrl}/results/${encodeURIComponent(id)}`, {
      headers: this.token ? { Authorization: `Bearer ${this.token}` } : undefined,
    });
  }

  // ── User ──
  async getUserProfile(): Promise<User> {
    if (DEMO_MODE) {
      await sleep(300);
      return {
        uid: 'user_001',
        email: 'student@university.edu',
        plan: 'free',
        generationsUsed: 12,
        createdAt: '2026-03-01T00:00:00Z',
        lastLogin: new Date().toISOString(),
      };
    }

    return fetchJson<User>(`${this.baseUrl}/me`, {
      headers: this.token ? { Authorization: `Bearer ${this.token}` } : undefined,
    });
  }
}

export const apiClient = new ApiClient(API_BASE);
