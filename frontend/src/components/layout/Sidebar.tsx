import { NavLink, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  History,
  Settings,
  LogOut,
  ChevronLeft,
  Cpu,
  Languages,
  Volume2,
  CheckCircle2,
  XCircle,
  Menu,
} from 'lucide-react';
import { useAuthStore } from '@/store/auth';
import { useAppStore } from '@/store/app';
import { apiClient } from '@/api/client';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/history', label: 'History', icon: History },
];

export function Sidebar() {
  const { user, logout } = useAuthStore();
  const {
    provider,
    setProvider,
    language,
    setLanguage,
    enableTts,
    setEnableTts,
    sidebarOpen,
    setSidebarOpen,
  } = useAppStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    apiClient.setToken(null);
    logout();
    navigate('/');
  };

  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-overlay z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Mobile toggle */}
      <button
        onClick={() => setSidebarOpen(true)}
        className="fixed top-4 left-4 z-50 lg:hidden p-2 rounded-lg bg-surface border border-border text-text-secondary hover:text-text"
        aria-label="Open sidebar"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Sidebar panel */}
      <motion.aside
        initial={false}
        animate={{ x: sidebarOpen ? 0 : -320 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className={cn(
          'fixed left-0 top-0 bottom-0 w-72 bg-surface border-r border-border z-50',
          'flex flex-col overflow-y-auto',
          'lg:translate-x-0 lg:static lg:z-auto'
        )}
      >
        {/* Header */}
        <div className="p-5 flex items-center justify-between border-b border-border">
          <NavLink to="/dashboard" className="flex items-center gap-2">
            <span className="gradient-text font-display font-extrabold text-2xl tracking-tight">
              AUDORA
            </span>
          </NavLink>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-muted hover:text-text"
            aria-label="Close sidebar"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                  isActive
                    ? 'bg-accent/[0.08] text-accent'
                    : 'text-text-secondary hover:text-text hover:bg-surface-hover'
                )
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Provider */}
        <div className="px-5 py-3 border-t border-border">
          <p className="text-xs font-mono uppercase tracking-widest text-muted mb-2 flex items-center gap-1.5">
            <Cpu className="w-3 h-3" /> Provider
          </p>
          <div className="flex gap-1 p-1 bg-bg-elevated rounded-lg">
            {(['groq', 'openai'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setProvider(p)}
                className={cn(
                  'flex-1 py-1.5 px-2 text-xs font-bold rounded-md transition-all',
                  provider === p
                    ? 'bg-accent text-bg'
                    : 'text-muted hover:text-text'
                )}
              >
                {p === 'groq' ? 'Groq (Free)' : 'OpenAI'}
              </button>
            ))}
          </div>
        </div>

        {/* Language */}
        <div className="px-5 py-3 border-t border-border">
          <p className="text-xs font-mono uppercase tracking-widest text-muted mb-2 flex items-center gap-1.5">
            <Languages className="w-3 h-3" /> Language
          </p>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value as any)}
            className="w-full rounded-lg border border-border bg-bg-elevated px-3 py-2 text-xs text-text appearance-none cursor-pointer focus:outline-none focus:border-accent"
          >
            {[
              'English', 'Spanish', 'French', 'German',
              'Arabic', 'Urdu', 'Hindi', 'Portuguese',
              'Japanese', 'Mandarin',
            ].map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
        </div>

        {/* TTS */}
        <div className="px-5 py-3 border-t border-border">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={enableTts}
              onChange={(e) => setEnableTts(e.target.checked)}
              className="rounded border-border accent-accent"
            />
            <Volume2 className="w-3.5 h-3.5 text-muted" />
            <span className="text-xs text-text-secondary">Audio notes</span>
          </label>
        </div>

        {/* Deps */}
        <div className="px-5 py-3 border-t border-border">
          <p className="text-xs font-mono uppercase tracking-widest text-muted mb-2">Dependencies</p>
          <div className="space-y-1">
            {[
              { label: 'Whisper', ok: true },
              { label: 'Embeddings', ok: true },
              { label: 'gTTS', ok: true },
              { label: 'OCR Stack', ok: false },
            ].map((d) => (
              <div key={d.label} className="flex items-center gap-2 text-xs">
                {d.ok ? (
                  <CheckCircle2 className="w-3 h-3 text-accent" />
                ) : (
                  <XCircle className="w-3 h-3 text-accent2" />
                )}
                <span className={d.ok ? 'text-text-secondary' : 'text-muted'}>{d.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* User */}
        <div className="p-5 border-t border-border">
          {user && (
            <div className="mb-3">
              <p className="text-sm font-medium text-text truncate">{user.email}</p>
              <p className="text-xs text-muted mt-0.5">
                {user.plan.charAt(0).toUpperCase() + user.plan.slice(1)} · {user.generationsUsed} generations
              </p>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-sm text-muted hover:text-accent2 transition-colors w-full"
          >
            <LogOut className="w-4 h-4" />
            Log out
          </button>
        </div>
      </motion.aside>
    </>
  );
}
