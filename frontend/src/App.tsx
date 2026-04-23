import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/api/client';
import { initializeConfig } from '@/store/config';
import { AppShell } from '@/components/layout/AppShell';
import { LandingPage } from '@/pages/Landing';
import { LoginPage, RegisterPage } from '@/pages/Auth';
import { DashboardPage } from '@/pages/Dashboard';
import { ResultsPage } from '@/pages/Results';
import { HistoryPage } from '@/pages/History';
import type { ReactNode } from 'react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000,
      refetchOnWindowFocus: false,
    },
  },
});

function ProtectedRoute({ children }: { children: ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function GuestRoute({ children }: { children: ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

function SessionBootstrap() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const idToken = useAuthStore((s) => s.idToken);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const expiresAt = useAuthStore((s) => s.expiresAt);
  const logout = useAuthStore((s) => s.logout);
  const setTokens = useAuthStore((s) => s.setTokens);

  useEffect(() => {
        // Initialize runtime config on app startup
        initializeConfig().catch((err) => {
          console.error('Failed to initialize config:', err);
        });
      }, []);

      useEffect(() => {
    let cancelled = false;

    const syncSession = async () => {
      if (!idToken) {
        apiClient.setToken(null);
        if (isAuthenticated) {
          logout();
        }
        return;
      }

      if (expiresAt && Date.now() > expiresAt) {
        if (refreshToken) {
          try {
            const refreshed = await apiClient.refreshSession(refreshToken);
            if (cancelled) return;
            apiClient.setToken(refreshed.idToken);
            setTokens(refreshed.idToken, refreshed.refreshToken, refreshed.expiresIn);
            return;
          } catch {
            // fall through to logout
          }
        }

        apiClient.setToken(null);
        logout();
        return;
      }

      apiClient.setToken(idToken);
    };

    void syncSession();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, idToken, refreshToken, expiresAt, logout, setTokens]);

  return null;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <SessionBootstrap />
        <Routes>
          <Route
            path="/"
            element={
              <GuestRoute>
                <LandingPage />
              </GuestRoute>
            }
          />
          <Route
            path="/login"
            element={
              <GuestRoute>
                <LoginPage />
              </GuestRoute>
            }
          />
          <Route
            path="/register"
            element={
              <GuestRoute>
                <RegisterPage />
              </GuestRoute>
            }
          />
          <Route
            element={
              <ProtectedRoute>
                <AppShell />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/results" element={<ResultsPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
