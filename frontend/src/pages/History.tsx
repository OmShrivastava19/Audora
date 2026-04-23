import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  History,
  Search,
  Calendar,
  Cpu,
  FileAudio,
  BookOpen,
  AlertTriangle,
  ArrowRight,
  LayoutGrid,
  List,
} from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { EmptyState, ErrorBanner } from '@/components/ui/Misc';
import { apiClient } from '@/api/client';
import { mockLectureHistory } from '@/api/mock-data';
import { formatDate } from '@/lib/utils';
import type { LectureHistoryItem } from '@/types';

const DEMO_MODE = import.meta.env.MODE === 'demo' || false;

export function HistoryPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [filterProvider, setFilterProvider] = useState<string>('all');
  const [history, setHistory] = useState<LectureHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');

    const loadHistory = async () => {
      if (DEMO_MODE) {
        setHistory(mockLectureHistory);
        setLoading(false);
        return;
      }

      try {
        const data = await apiClient.getLectureHistory();
        if (cancelled) return;
        setHistory(data);
      } catch (err: any) {
        if (cancelled) return;
        setHistory([]);
        setError(err?.message || 'Could not load lecture history.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void loadHistory();

    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = history.filter((item) => {
    const matchSearch =
      !search ||
      item.title.toLowerCase().includes(search.toLowerCase()) ||
      item.lecture_filename.toLowerCase().includes(search.toLowerCase()) ||
      item.course?.toLowerCase().includes(search.toLowerCase());
    const matchProvider = filterProvider === 'all' || item.provider === filterProvider;
    return matchSearch && matchProvider;
  });

  const openResult = (item: LectureHistoryItem) => {
    navigate(`/results?id=${item.id}`);
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-info-muted flex items-center justify-center">
          <History className="w-5 h-5 text-info" />
        </div>
        <div>
          <h1 className="font-display font-extrabold text-2xl text-text">Lecture History</h1>
          <p className="text-sm text-muted">{history.length} generations</p>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <Input
            placeholder="Search by title, filename, or course..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            icon={<Search className="w-4 h-4" />}
          />
        </div>
        <div className="flex gap-2">
          {['all', 'groq', 'openai'].map((p) => (
            <button
              key={p}
              onClick={() => setFilterProvider(p)}
              className={`px-3 py-2 rounded-lg text-xs font-bold transition-all ${
                filterProvider === p
                  ? 'bg-accent text-bg'
                  : 'bg-surface border border-border text-muted hover:text-text'
              }`}
            >
              {p === 'all' ? 'All' : p === 'groq' ? 'Groq' : 'OpenAI'}
            </button>
          ))}
          <div className="flex gap-1 p-1 bg-surface border border-border rounded-lg">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded ${
                viewMode === 'grid' ? 'bg-accent/10 text-accent' : 'text-muted'
              }`}
              aria-label="Grid view"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded ${
                viewMode === 'list' ? 'bg-accent/10 text-accent' : 'text-muted'
              }`}
              aria-label="List view"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <EmptyState
          icon={<History className="w-12 h-12" />}
          title="Loading history"
          description="Fetching lecture history from the server."
        />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<History className="w-12 h-12" />}
          title="No lectures found"
          description={
            error
              ? 'The server did not return any lectures.'
              : 'Try adjusting your search or filters.'
          }
        />
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Card hover onClick={() => openResult(item)} className="h-full flex flex-col">
                <div className="flex items-start justify-between mb-3">
                  <Badge variant={item.provider === 'groq' ? 'accent' : 'info'}>
                    {item.provider}
                  </Badge>
                  <Badge variant="muted">{item.language}</Badge>
                </div>
                <h3 className="font-display font-bold text-sm text-text mb-2 line-clamp-2">
                  {item.title}
                </h3>
                {item.course && <p className="text-xs text-muted mb-3">{item.course}</p>}
                <div className="mt-auto pt-3 border-t border-border flex items-center justify-between">
                  <div className="flex items-center gap-3 text-xs text-muted">
                    <span className="flex items-center gap-1">
                      <BookOpen className="w-3 h-3" /> {item.notes_count}
                    </span>
                    <span className="flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" /> {item.exam_hints_count}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-muted">
                    <Calendar className="w-3 h-3" />
                    {formatDate(item.created_at)}
                  </div>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.03 }}
            >
              <Card hover onClick={() => openResult(item)} className="flex items-center gap-4 py-3">
                <div className="w-9 h-9 rounded-lg bg-surface-hover flex items-center justify-center flex-shrink-0">
                  <FileAudio className="w-4 h-4 text-muted" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-text truncate">{item.title}</p>
                  <p className="text-xs text-muted truncate">
                    {item.lecture_filename} {item.course ? `· ${item.course}` : ''}
                  </p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <Badge variant={item.provider === 'groq' ? 'accent' : 'info'} size="sm">
                    {item.provider}
                  </Badge>
                  <span className="text-xs text-muted hidden sm:inline">
                    {formatDate(item.created_at)}
                  </span>
                  <ArrowRight className="w-4 h-4 text-muted" />
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
