import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  BookOpen,
  Zap,
  ShieldCheck,
  Brain,
  BarChart3,
  Download,
  ArrowRight,
  GraduationCap,
  Sparkles,
  Target,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.12 } },
} as const;

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
} as const;

const FEATURES = [
  {
    icon: <Brain className="w-6 h-6" />,
    title: 'AI-Powered Notes',
    description: 'Structured, syllabus-grounded notes with source citations from your lecture transcript.',
    color: 'text-accent',
    bg: 'bg-accent-muted',
  },
  {
    icon: <Target className="w-6 h-6" />,
    title: 'Exam Radar',
    description: 'Automatic detection of exam hints, assessment cues, and important topics flagged by the instructor.',
    color: 'text-accent2',
    bg: 'bg-accent2-muted',
  },
  {
    icon: <BarChart3 className="w-6 h-6" />,
    title: 'Syllabus Coverage',
    description: 'See exactly which topics were covered, partially mentioned, or completely missing from the lecture.',
    color: 'text-accent3',
    bg: 'bg-accent3-muted',
  },
  {
    icon: <Sparkles className="w-6 h-6" />,
    title: 'Study Practice',
    description: 'Auto-generated flashcards and mixed quizzes (MCQ, short answer, true/false) for active recall.',
    color: 'text-info',
    bg: 'bg-info-muted',
  },
  {
    icon: <ShieldCheck className="w-6 h-6" />,
    title: 'Confidence Scoring',
    description: 'Every note includes a confidence score and reasoning — so you know what to trust and what to verify.',
    color: 'text-accent',
    bg: 'bg-accent-muted',
  },
  {
    icon: <Download className="w-6 h-6" />,
    title: 'Export Everything',
    description: 'Download notes as Markdown or JSON, transcripts as TXT, flashcards and quizzes as JSON.',
    color: 'text-accent3',
    bg: 'bg-accent3-muted',
  },
];

export function LandingPage() {
  return (
    <div className="min-h-dvh noise-bg">
      {/* Nav */}
      <nav className="fixed top-0 inset-x-0 z-50 glass border-b border-border/40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <GraduationCap className="w-6 h-6 text-accent" />
            <span className="gradient-text font-display font-extrabold text-xl tracking-tight">
              AUDORA
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <Link to="/login">
              <Button variant="ghost" size="sm">Log in</Button>
            </Link>
            <Link to="/register">
              <Button size="sm">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-32 pb-20 px-6 overflow-hidden">
        {/* Background shapes */}
        <div className="absolute top-20 left-1/4 w-96 h-96 bg-accent/5 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute top-40 right-1/4 w-80 h-80 bg-info/5 rounded-full blur-[100px] pointer-events-none" />

        <motion.div
          variants={stagger}
          initial="hidden"
          animate="visible"
          className="max-w-4xl mx-auto text-center relative z-10"
        >
          <motion.div variants={fadeUp}>
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent-muted border border-accent/20 text-accent text-xs font-mono font-medium tracking-wider uppercase mb-6">
              <Zap className="w-3 h-3" /> AI-Powered Lecture Intelligence
            </span>
          </motion.div>

          <motion.h1
            variants={fadeUp}
            className="font-display font-extrabold text-5xl sm:text-6xl lg:text-7xl tracking-tight text-text leading-[1.1] text-balance"
          >
            Transform lectures into{' '}
            <span className="gradient-text">structured intelligence</span>
          </motion.h1>

          <motion.p
            variants={fadeUp}
            className="mt-6 text-lg sm:text-xl text-text-secondary max-w-2xl mx-auto leading-relaxed"
          >
            Upload a lecture recording. Get syllabus-grounded notes, exam hints,
            coverage analysis, flashcards, and quizzes — all powered by AI.
          </motion.p>

          <motion.div variants={fadeUp} className="flex items-center justify-center gap-4 mt-10">
            <Link to="/register">
              <Button size="lg" className="text-base px-8">
                Start free <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="outline" size="lg" className="text-base px-8">
                Log in
              </Button>
            </Link>
          </motion.div>

          {/* Demo preview card */}
          <motion.div
            variants={fadeUp}
            className="mt-16 rounded-2xl border border-border bg-surface/80 backdrop-blur-sm p-1 shadow-lg max-w-3xl mx-auto"
          >
            <div className="rounded-xl bg-bg p-6 space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-accent2/60" />
                <div className="w-3 h-3 rounded-full bg-accent3/60" />
                <div className="w-3 h-3 rounded-full bg-accent/60" />
                <span className="ml-2 text-xs text-muted font-mono">audora — results workspace</span>
              </div>
              <div className="grid grid-cols-4 gap-3">
                {[
                  { label: 'Provider', value: 'Groq' },
                  { label: 'Language', value: 'English' },
                  { label: 'Noise Removed', value: '7' },
                  { label: 'Exam Hints', value: '3' },
                ].map((m) => (
                  <div key={m.label} className="rounded-lg bg-surface border border-border p-3">
                    <p className="text-[10px] font-mono uppercase text-muted tracking-wider">{m.label}</p>
                    <p className="text-lg font-display font-bold text-text mt-1">{m.value}</p>
                  </div>
                ))}
              </div>
              <div className="rounded-lg bg-surface border-l-4 border-l-accent border border-border p-4">
                <p className="text-xs font-mono text-accent tracking-widest uppercase mb-1">Executive Summary</p>
                <p className="text-sm text-text-secondary leading-relaxed">
                  This lecture covered binary search trees, their properties and time complexities, tree traversal methods,
                  and self-balancing BST variants including AVL trees...
                </p>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* Features */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-100px' }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <p className="font-mono text-xs uppercase tracking-[4px] text-accent mb-3">Features</p>
            <h2 className="font-display font-extrabold text-3xl sm:text-4xl text-text">
              Everything you need to ace your exams
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ duration: 0.5, delay: i * 0.08 }}
                className="group rounded-2xl border border-border bg-surface p-6 hover:border-border-focus hover:bg-surface-hover transition-all duration-300"
              >
                <div className={`w-12 h-12 rounded-xl ${feature.bg} flex items-center justify-center ${feature.color} mb-4 group-hover:scale-110 transition-transform`}>
                  {feature.icon}
                </div>
                <h3 className="font-display font-bold text-lg text-text mb-2">{feature.title}</h3>
                <p className="text-sm text-text-secondary leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="max-w-3xl mx-auto text-center rounded-2xl border border-border bg-surface p-12 relative overflow-hidden"
        >
          <div className="absolute top-0 left-1/3 w-64 h-64 bg-accent/5 rounded-full blur-[80px] pointer-events-none" />
          <div className="relative z-10">
            <BookOpen className="w-10 h-10 text-accent mx-auto mb-4" />
            <h2 className="font-display font-extrabold text-3xl text-text mb-3">
              Ready to study smarter?
            </h2>
            <p className="text-text-secondary mb-8 max-w-md mx-auto">
              Join students using Audora to transform lecture recordings into structured study materials in minutes.
            </p>
            <Link to="/register">
              <Button size="lg" className="text-base px-10">
                Get Started Free <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-muted">
          <div className="flex items-center gap-2">
            <GraduationCap className="w-4 h-4 text-accent" />
            <span className="font-display font-bold gradient-text">AUDORA</span>
            <span>· Curriculum Grounded AI</span>
          </div>
          <p>© 2026 Audora. Built for students, by students.</p>
        </div>
      </footer>
    </div>
  );
}
