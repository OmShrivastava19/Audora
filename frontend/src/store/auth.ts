import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AuthState, User } from '@/types';

interface AuthStore extends AuthState {
  login: (user: User, idToken: string, refreshToken: string, expiresIn: number) => void;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
  setTokens: (idToken: string, refreshToken: string, expiresIn: number) => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      user: null,
      idToken: null,
      refreshToken: null,
      expiresAt: null,

      login: (user, idToken, refreshToken, expiresIn) =>
        set({
          isAuthenticated: true,
          user,
          idToken,
          refreshToken,
          expiresAt: Date.now() + expiresIn * 1000,
        }),
      logout: () =>
        set({
          isAuthenticated: false,
          user: null,
          idToken: null,
          refreshToken: null,
          expiresAt: null,
        }),

      updateUser: (updates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),

      setTokens: (idToken, refreshToken, expiresIn) =>
        set({
          idToken,
          refreshToken,
          expiresAt: Date.now() + expiresIn * 1000,
        }),
    }),
    {
      name: 'audora-auth',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        idToken: state.idToken,
        refreshToken: state.refreshToken,
        expiresAt: state.expiresAt,
      }),
    }
  )
);
