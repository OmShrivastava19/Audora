import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Toaster } from 'react-hot-toast';

export function AppShell() {
  return (
    <div className="flex min-h-dvh noise-bg">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8 pt-16 lg:pt-8">
          <Outlet />
        </div>
      </main>
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#161a23',
            color: '#e8eaf2',
            border: '1px solid #252b3a',
            fontFamily: '"Space Grotesk", sans-serif',
            fontSize: '0.875rem',
          },
          success: {
            iconTheme: { primary: '#4fffb0', secondary: '#0a0c10' },
          },
          error: {
            iconTheme: { primary: '#ff6b6b', secondary: '#0a0c10' },
          },
        }}
      />
    </div>
  );
}
