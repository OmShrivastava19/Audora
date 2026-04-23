// ── All DTOs and interfaces for Audora ──

export interface User {
  uid: string;
  email: string;
  plan: 'free' | 'pro' | 'team';
  generationsUsed: number;
  createdAt: string;
  lastLogin: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  idToken: string | null;
  refreshToken: string | null;
  expiresAt: number | null;
}

export interface TranscriptSegment {
  segment_id: string;
  start_sec: number;
  end_sec: number;
  text: string;
}

export interface NoteReference {
  segment_id: string;
  start_sec: number;
  end_sec: number;
  quote: string;
  confidence?: number;
}

export interface StructuredNote {
  module: string;
  content: string;
  references: NoteReference[];
  source_refs: string[];
  confidence_score: number;
  confidence_label: 'HIGH' | 'MEDIUM' | 'LOW';
  confidence_reason: string;
}

export interface ExamHint {
  hint: string;
  module: string;
  urgency: 'HIGH' | 'MEDIUM';
  reason: string;
}

export interface CoverageModule {
  module_name: string;
  coverage_percent: number;
  status: 'Covered' | 'Partial' | 'Missing';
  evidence_count: number;
  top_evidence_snippets: Array<{
    segment_id: string;
    start_sec: number;
    end_sec: number;
    text: string;
    score: number;
  }>;
}

export interface CoverageSummary {
  covered: number;
  partial: number;
  missing: number;
  total: number;
}

export interface SyllabusCoverage {
  modules: CoverageModule[];
  summary: CoverageSummary;
  error?: string;
}

export interface PracticeFlashcard {
  question: string;
  answer: string;
  module: string;
  difficulty: 'easy' | 'medium' | 'hard';
}

export interface PracticeQuizItem {
  id: string;
  type: 'mcq' | 'short_answer' | 'true_false';
  module: string;
  difficulty: 'easy' | 'medium' | 'hard';
  question: string;
  explanation: string;
  options?: string[];
  correct_index?: number;
  answer?: string | boolean;
}

export interface PracticePayload {
  metadata: {
    title: string;
    language: string;
    generated_from_modules: string[];
  };
  flashcards: PracticeFlashcard[];
  quiz: PracticeQuizItem[];
}

export interface GenerationResult {
  id: string;
  title: string;
  summary: string;
  filtered_count: number;
  language: string;
  notes: StructuredNote[];
  exam_radar: ExamHint[];
  transcript_segments: TranscriptSegment[];
  transcript_text: string;
  syllabus_coverage: SyllabusCoverage;
  practice: PracticePayload;
  provider: 'groq' | 'openai';
  created_at: string;
  lecture_filename: string;
  audio_notes_url?: string;
}

export interface PipelineStage {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'done' | 'error';
  progress?: number;
}

export type Provider = 'groq' | 'openai';

export type Language = 
  | 'English' | 'Spanish' | 'French' | 'German' 
  | 'Arabic' | 'Urdu' | 'Hindi' | 'Portuguese' 
  | 'Japanese' | 'Mandarin';

export const LANGUAGES: Record<Language, { iso: string; tts: string }> = {
  English: { iso: 'en', tts: 'en' },
  Spanish: { iso: 'es', tts: 'es' },
  French: { iso: 'fr', tts: 'fr' },
  German: { iso: 'de', tts: 'de' },
  Arabic: { iso: 'ar', tts: 'ar' },
  Urdu: { iso: 'ur', tts: 'ur' },
  Hindi: { iso: 'hi', tts: 'hi' },
  Portuguese: { iso: 'pt', tts: 'pt' },
  Japanese: { iso: 'ja', tts: 'ja' },
  Mandarin: { iso: 'zh-CN', tts: 'zh' },
};

export const SUPPORTED_AUDIO_EXTENSIONS = [
  '.mp3', '.mp4', '.m4a', '.wav', '.ogg', '.flac', '.webm', '.mpeg', '.mpga',
] as const;

export interface LectureHistoryItem {
  id: string;
  title: string;
  provider: Provider;
  language: Language;
  lecture_filename: string;
  created_at: string;
  notes_count: number;
  exam_hints_count: number;
  course?: string;
}
