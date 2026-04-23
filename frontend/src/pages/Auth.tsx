import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { GraduationCap, Mail, Lock, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ErrorBanner } from '@/components/ui/Misc';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/api/client';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState('');
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { user, idToken, refreshToken, expiresIn } = await apiClient.login(email, password);
      apiClient.setToken(idToken);
      login(user, idToken, refreshToken, expiresIn);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError('');
    setGoogleLoading(true);
    try {
      const { user, idToken, refreshToken, expiresIn } = await apiClient.loginWithGoogle();
      apiClient.setToken(idToken);
      login(user, idToken, refreshToken, expiresIn);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Google sign-in failed.');
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <div className="min-h-dvh flex items-center justify-center px-6 noise-bg">
      <div className="absolute top-20 left-1/3 w-80 h-80 bg-accent/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-20 right-1/3 w-64 h-64 bg-info/5 rounded-full blur-[100px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md relative z-10"
      >
        <Link to="/" className="flex items-center justify-center gap-2 mb-8">
          <GraduationCap className="w-7 h-7 text-accent" />
          <span className="gradient-text font-display font-extrabold text-3xl tracking-tight">
            AUDORA
          </span>
        </Link>

        <div className="rounded-2xl border border-border bg-surface p-8">
          <h1 className="font-display font-bold text-2xl text-text text-center mb-1">
            Welcome back
          </h1>
          <p className="text-sm text-muted text-center mb-6">
            Sign in to your account to continue
          </p>

          {error && <ErrorBanner message={error} onDismiss={() => setError('')} className="mb-4" />}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email"
              type="email"
              placeholder="you@university.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              icon={<Mail className="w-4 h-4" />}
              required
              autoComplete="email"
            />
            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={<Lock className="w-4 h-4" />}
              required
              autoComplete="current-password"
            />
            <Button type="submit" fullWidth loading={loading} className="mt-2">
              Sign in <ArrowRight className="w-4 h-4" />
            </Button>
          </form>

          <div className="flex items-center gap-4 my-6">
            <div className="h-px bg-border flex-1" />
            <span className="text-xs text-muted">or</span>
            <div className="h-px bg-border flex-1" />
          </div>

          <Button
            variant="secondary"
            fullWidth
            loading={googleLoading}
            onClick={handleGoogleLogin}
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            Continue with Google
          </Button>
        </div>

        <p className="text-center text-sm text-muted mt-6">
          Don't have an account?{' '}
          <Link to="/register" className="text-accent hover:underline font-medium">
            Sign up
          </Link>
        </p>
      </motion.div>
    </div>
  );
}

export function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }
    setLoading(true);
    try {
      const { user, idToken, refreshToken, expiresIn } = await apiClient.register(email, password);
      apiClient.setToken(idToken);
      login(user, idToken, refreshToken, expiresIn);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-dvh flex items-center justify-center px-6 noise-bg">
      <div className="absolute top-32 right-1/4 w-80 h-80 bg-accent/5 rounded-full blur-[120px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md relative z-10"
      >
        <Link to="/" className="flex items-center justify-center gap-2 mb-8">
          <GraduationCap className="w-7 h-7 text-accent" />
          <span className="gradient-text font-display font-extrabold text-3xl tracking-tight">
            AUDORA
          </span>
        </Link>

        <div className="rounded-2xl border border-border bg-surface p-8">
          <h1 className="font-display font-bold text-2xl text-text text-center mb-1">
            Create account
          </h1>
          <p className="text-sm text-muted text-center mb-6">
            Start transforming your lectures into study material
          </p>

          {error && <ErrorBanner message={error} onDismiss={() => setError('')} className="mb-4" />}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email"
              type="email"
              placeholder="you@university.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              icon={<Mail className="w-4 h-4" />}
              required
              autoComplete="email"
            />
            <Input
              label="Password"
              type="password"
              placeholder="Min. 6 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={<Lock className="w-4 h-4" />}
              required
              autoComplete="new-password"
            />
            <Button type="submit" fullWidth loading={loading} className="mt-2">
              Create account <ArrowRight className="w-4 h-4" />
            </Button>
          </form>
        </div>

        <p className="text-center text-sm text-muted mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-accent hover:underline font-medium">
            Sign in
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
