"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                               AUDORA MVP                                     ║
║              Syllabus-Aware AI Lecture Intelligence System                   ║
║                                                                              ║
║                                                                              ║
║  STACK:                                                                      ║
║  • Transcription : Groq Whisper API (free tier, no ffmpeg, cloud-fast)       ║
║  • Embeddings    : sentence-transformers all-MiniLM-L6-v2 (local, 80MB)      ║
║  • Vector Store  : FAISS-CPU (local, in-memory)                              ║
║  • LLM Reasoning : Groq LLaMA 3.3-70B (free tier, 14400 req/day)             ║
║  • TTS Output    : gTTS (free Google TTS, internet only, no key needed)      ║
║                                                                              ║
║  ONE FREE KEY DOES EVERYTHING:                                               ║
║                                                                              ║
║  GROQ KEY    → https://console.groq.com                                      ║
║    Sign up free → "API Keys" → "Create API Key" → copy it                    ║
║    Free limits:                                                              ║
║      • 7,200 minutes of audio/day  (Whisper transcription)                   ║
║      • 14,400 requests/day         (LLaMA note generation)                   ║
║      • 1,000,000 tokens/day        (LLaMA note generation)                   ║
║                                                                              ║
║  INSTALL:                                                                    ║
║    pip install groq sentence-transformers faiss-cpu numpy PyPDF2 gTTS        ║
║                streamlit python-dotenv                                       ║
║                                                                              ║
║  RUN:                                                                        ║
║    streamlit run audora.py                                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import re
import traceback
from pathlib import Path
from io import BytesIO

import streamlit as st

# ── Load .env if present ───────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ══════════════════════════════════════════════════════════════════════════════
# IMPORTS — all pure Python, no system dependencies
# ══════════════════════════════════════════════════════════════════════════════

# 1. Groq (free Whisper transcription + LLaMA notes — one key for everything)
try:
    from groq import Groq
    GROQ_OK = True
    GROQ_ERROR = None
except ImportError as e:
    Groq = None
    GROQ_OK = False
    GROQ_ERROR = str(e)

# 2. Sentence Transformers (free local embeddings, ~80MB model)
try:
    from sentence_transformers import SentenceTransformer
    SBERT_OK = True
    SBERT_ERROR = None
except ImportError as e:
    SentenceTransformer = None
    SBERT_OK = False
    SBERT_ERROR = str(e)

# 3. FAISS (free local vector store)
try:
    import faiss
    import numpy as np
    FAISS_OK = True
    FAISS_ERROR = None
except ImportError as e:
    faiss = None
    np = None
    FAISS_OK = False
    FAISS_ERROR = str(e)

# 4. PyPDF2 (free PDF text extraction)
try:
    import PyPDF2
    PYPDF2_OK = True
    PYPDF2_ERROR = None
except ImportError as e:
    PyPDF2 = None
    PYPDF2_OK = False
    PYPDF2_ERROR = str(e)

# 5. gTTS (free text-to-speech, uses Google Translate TTS endpoint)
try:
    from gtts import gTTS
    GTTS_OK = True
    GTTS_ERROR = None
except ImportError as e:
    gTTS = None
    GTTS_OK = False
    GTTS_ERROR = str(e)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & STYLING
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Audora — Free Lecture Intelligence",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@400;500&family=Inter:wght@300;400;500&display=swap');

  :root {
    --bg:      #0d0f14;
    --surface: #161a23;
    --border:  #252b3a;
    --accent:  #4fffb0;
    --accent2: #ff6b6b;
    --accent3: #ffd166;
    --info:    #00c4ff;
    --text:    #e8eaf2;
    --muted:   #7b82a0;
    --radius:  12px;
  }
  html, body, [class*="css"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif;
  }
  .main .block-container { padding: 2rem 3rem; max-width: 1280px; }

  .audora-wordmark {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: clamp(2.5rem, 5vw, 4rem);
    letter-spacing: -2px;
    background: linear-gradient(135deg, var(--accent) 0%, #00c4ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
  }
  .audora-tagline {
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    color: var(--muted);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 0.3rem;
  }
  .pill {
    display: inline-block;
    border-radius: 20px;
    padding: 2px 12px;
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-left: 0.5rem;
    vertical-align: middle;
  }
  .pill-green { background: rgba(79,255,176,0.12); border: 1px solid var(--accent); color: var(--accent); }
  .pill-blue  { background: rgba(0,196,255,0.12);  border: 1px solid var(--info);   color: var(--info); }
  .pill-orange { background: rgba(255,209,102,0.12); border: 1px solid var(--accent3); color: var(--accent3); }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.1rem;
  }
  .card-green  { border-left: 4px solid var(--accent); }
  .card-red    { border-left: 4px solid var(--accent2); }
  .card-yellow { border-left: 4px solid var(--accent3); }
  .card-blue   { border-left: 4px solid var(--info); }

  .section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 0.7rem;
  }

  /* Key setup guide */
  .key-step {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    margin-bottom: 0.6rem;
  }
  .key-num {
    background: var(--accent);
    color: #0d0f14;
    border-radius: 50%;
    width: 22px;
    height: 22px;
    min-width: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 0.75rem;
    margin-top: 1px;
  }

  /* Radar badges */
  .rbadge {
    display: inline-block;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.72rem;
    font-family: 'DM Mono', monospace;
    font-weight: 500;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-right: 0.4rem;
    margin-bottom: 0.3rem;
  }
  .rbadge-high { border: 1px solid #ff4444; color: #ff4444; background: rgba(255,68,68,0.12); }
  .rbadge-med  { border: 1px solid var(--accent3); color: var(--accent3); background: rgba(255,209,102,0.10); }
  .rbadge-mod  { border: 1px solid var(--muted); color: var(--muted); background: transparent; }

  /* Notes body */
  .notes-body { font-family: 'Inter', sans-serif; font-size: 1rem; line-height: 1.85; }
  .notes-body h2 {
    font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 700;
    color: var(--accent); margin-top: 1.5rem; margin-bottom: 0.5rem;
    border-bottom: 1px solid var(--border); padding-bottom: 0.35rem;
  }
  .notes-body h3 { font-family: 'Syne', sans-serif; font-size: 1rem; color: #7ee8c8; margin-top: 1.1rem; }
  .notes-body ul { padding-left: 1.3rem; }
  .notes-body li { margin-bottom: 0.3rem; }
  .notes-body strong { color: #ffd166; }
  .notes-body code  { background: #1e2433; border-radius: 4px; padding: 1px 6px; font-size: 0.88em; }

  /* Uploader */
  [data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 2px dashed var(--border) !important;
    border-radius: var(--radius) !important;
  }
  [data-testid="stFileUploader"]:hover { border-color: var(--accent) !important; }

  /* Button */
  .stButton > button {
    background: var(--accent) !important; color: #0d0f14 !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    font-size: 1rem !important; border: none !important;
    border-radius: 8px !important; padding: 0.65rem 2rem !important;
    width: 100%; letter-spacing: 0.5px; transition: opacity 0.2s;
  }
  .stButton > button:hover   { opacity: 0.85 !important; }
  .stButton > button:disabled { opacity: 0.35 !important; }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
  }
  .stTextInput > div > div > input, .stSelectbox > div > div {
    background: var(--bg) !important; color: var(--text) !important;
    border-color: var(--border) !important; border-radius: 8px !important;
  }
  .stProgress > div > div { background: var(--accent) !important; }
  hr { border-color: var(--border) !important; }
  *:focus-visible { outline: 2px solid var(--accent) !important; outline-offset: 2px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# AUDORA SYSTEM PROMPT
# ══════════════════════════════════════════════════════════════════════════════

AUDORA_SYSTEM_PROMPT = """
You are Audora, an elite academic note-taking AI. Transform a raw lecture
transcript into structured, high-signal study notes guided by the course syllabus.

CORE DIRECTIVES
───────────────
1. NOISE GATE — DISCARD completely, do not mention or summarise:
   • Greetings, farewells, small-talk
   • Administrative announcements (room changes, deadlines unrelated to content)
   • Attendance & roll-call
   • Disciplinary remarks
   • Jokes, off-topic tangents, personal anecdotes
   • Filler words ("um", "uh", "you know", "basically", "so yeah")

2. SYLLABUS MAPPING — Use ONLY official module/topic headers from the
   SYLLABUS CONTEXT below. Never invent module names. If content does not
   match any module, use the closest match and append "(Extended Coverage)".

3. EXAM RADAR — Flag urgency signals. Triggers include:
   "mid-term", "final", "quiz", "assignment", "paper", "project",
   "will be tested", "remember this", "important", "key concept",
   "you need to know", "exam", "marks", "graded", "this comes up".
   HIGH urgency = explicit assessment reference or direct imperative.
   MEDIUM urgency = relative importance marker.

4. MULTILINGUAL — If a target language is specified, write all notes and
   summaries in that language. Keep technical terms in English with
   translations in parentheses.

OUTPUT — Return ONLY valid JSON. No markdown fences. Start with { end with }:

{
  "title": "<Lecture title inferred from content>",
  "summary": "<2-3 sentence executive summary of the lecture>",
  "notes": [
    {
      "module": "<Exact syllabus module name>",
      "content": "<Structured markdown: ## headings, bullet points, **bold** key terms>"
    }
  ],
  "exam_radar": [
    {
      "hint": "<Cleaned verbatim exam hint from lecturer>",
      "module": "<Relevant module name>",
      "urgency": "HIGH | MEDIUM",
      "reason": "<Why this was flagged>"
    }
  ],
  "filtered_count": <integer — noise segments removed>,
  "language": "<ISO 639-1 code>"
}
"""

# ══════════════════════════════════════════════════════════════════════════════
# KEY HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def get_env_key(name: str) -> str:
    """Fetch key from environment or Streamlit secrets."""
    val = os.getenv(name, "").strip()
    if not val:
        try:
            val = (st.secrets.get(name, "") or "").strip()
        except Exception:
            pass
    return val


# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT 1 — TRANSCRIPTION via Groq Whisper (free, no ffmpeg needed)
# ══════════════════════════════════════════════════════════════════════════════

def transcribe_with_groq(audio_bytes: bytes, filename: str, groq_key: str) -> str:
    """
    GROQ WHISPER TRANSCRIPTION — Why this solves the Windows/ffmpeg problem:
    ─────────────────────────────────────────────────────────────────────────
    • Groq runs Whisper on their servers — your laptop does zero audio decoding.
    • No ffmpeg binary needed anywhere on the system.
    • Groq's free tier: 7,200 audio minutes/day (= 120 hours).
    • Speed: typically 10-30x faster than local Whisper.
    • Supports MP3, MP4, WAV, M4A, OGG, FLAC, WEBM natively.
    • Works with both audio AND video files (transcribes first audio track).
    """
    if not GROQ_OK:
        raise RuntimeError("groq package not installed.\nRun: pip install groq")
    if not groq_key:
        raise ValueError("Groq API key is missing. Get a free key at https://console.groq.com")

    client = Groq(api_key=groq_key)

    suffix = Path(filename).suffix.lower() or ".mp3"
    content_type_map = {
        ".mp3":  "audio/mpeg",
        ".mp4":  "audio/mp4",
        ".m4a":  "audio/mp4",
        ".wav":  "audio/wav",
        ".ogg":  "audio/ogg",
        ".flac": "audio/flac",
        ".webm": "audio/webm",
        ".mpeg": "audio/mpeg",
        ".mpga": "audio/mpeg",
    }
    content_type = content_type_map.get(suffix, "audio/mpeg")

    # ── File size guard (Groq free tier limit: 25MB per request) ──────────────
    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > 25:
        raise ValueError(
            f"Audio/video file is {size_mb:.1f}MB. Groq's free tier accepts up to 25MB per request.\n"
            f"Tip: Compress to 64kbps mono MP3 — speech quality is preserved and size drops ~70%."
        )

    transcription = client.audio.transcriptions.create(
        model="whisper-large-v3-turbo",   # Groq's fastest free Whisper model
        file=(filename, audio_bytes, content_type),
        response_format="text",            # plain string, no timestamps needed
        language=None,                     # auto-detect language
    )

    return str(transcription).strip()


# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT 2 — EMBEDDINGS + VECTOR STORE (local, free, no API key)
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner="⚙️ Loading embedding model (80MB, first run only)…")
def load_embedding_model():
    """
    Load sentence-transformers locally.
    'all-MiniLM-L6-v2':
      • Size: ~80MB download, cached after first run
      • RAM: ~200MB when loaded — fine for 8GB laptops
      • Speed: embeds a 600-word chunk in ~50ms on CPU
    """
    if not SBERT_OK:
        return None
    return SentenceTransformer("all-MiniLM-L6-v2")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> list[str]:
    """Split syllabus text into overlapping chunks for FAISS indexing."""
    if not text.strip():
        return []

    for sep in ["\n\n", "\n", ". ", " "]:
        if sep in text:
            raw = text.split(sep)
            chunks, current = [], ""
            for part in raw:
                piece = (current + sep + part) if current else part
                if len(piece) <= chunk_size:
                    current = piece
                else:
                    if current.strip():
                        chunks.append(current.strip())
                    current = part
            if current.strip():
                chunks.append(current.strip())

            overlapped = []
            for i, c in enumerate(chunks):
                if i == 0:
                    overlapped.append(c)
                else:
                    tail = chunks[i - 1][-overlap:]
                    overlapped.append((tail + " " + c).strip())
            return [c for c in overlapped if c.strip()]

    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]


class SyllabusVectorStore:
    """
    Lightweight FAISS vector store backed by sentence-transformers.
    Uses cosine similarity (inner product on L2-normalised vectors).
    RAM budget: ~200MB embedding model + <1MB index = fine for 8GB laptops.
    """

    def __init__(self, chunks: list[str], model):
        self.chunks = chunks
        self.model = model

        embeddings = model.encode(
            chunks,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
        ).astype("float32")

        faiss.normalize_L2(embeddings)
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)

    def search(self, query: str, k: int = 8) -> list[str]:
        k = min(k, len(self.chunks))
        q_vec = self.model.encode(
            [query], show_progress_bar=False, convert_to_numpy=True
        ).astype("float32")
        faiss.normalize_L2(q_vec)
        _, idxs = self.index.search(q_vec, k)
        return [self.chunks[i] for i in idxs[0] if 0 <= i < len(self.chunks)]


def build_vector_store(syllabus_text: str) -> SyllabusVectorStore | None:
    if not SBERT_OK or not FAISS_OK:
        return None
    model = load_embedding_model()
    if model is None:
        return None
    chunks = chunk_text(syllabus_text)
    if not chunks:
        return None
    return SyllabusVectorStore(chunks, model)


def get_syllabus_context(store: SyllabusVectorStore | None, query: str) -> str:
    if store is None:
        return ""
    results = store.search(query, k=8)
    return "\n---\n".join(results)


# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT 3 — PDF EXTRACTION (free, pure Python)
# ══════════════════════════════════════════════════════════════════════════════

def extract_pdf_text(pdf_bytes: bytes) -> str:
    if not PYPDF2_OK:
        return ""
    try:
        reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
        pages = [p.extract_text() for p in reader.pages if p.extract_text()]
        return "\n\n".join(pages).strip()
    except Exception as e:
        st.warning(f"PDF extraction issue: {e}")
        return ""


# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT 4 — LLM REASONING via Groq LLaMA (free tier, same key!)
# ══════════════════════════════════════════════════════════════════════════════

def generate_notes_with_groq_llm(
    transcript: str,
    syllabus_context: str,
    groq_key: str,
    target_language: str = "English",
) -> dict:
    """
    GROQ LLaMA NOTE GENERATION
    ───────────────────────────
    Uses the same Groq key as transcription — no extra API key needed.

    Why Groq LLaMA instead of Gemini:
      • Gemini free tier slashed to limit: 0 in late 2025 (quota errors)
      • Groq free tier: 14,400 requests/day, 1,000,000 tokens/day
      • Model: llama-3.3-70b-versatile (128k context window)
      • Speed: ~300 tokens/sec — extremely fast
      • No credit card, no billing, genuinely free
      • One key (gsk_...) handles BOTH transcription AND note generation
    """
    if not GROQ_OK:
        raise RuntimeError("groq package not installed. Run: pip install groq")
    if not groq_key:
        raise ValueError("Groq API key is missing. Get a free key at https://console.groq.com")

    language_line = (
        f"Write ALL notes and the summary in {target_language}. "
        "Keep technical terms in English with translations in parentheses."
        if target_language.lower() != "english" else ""
    )

    full_prompt = f"""{AUDORA_SYSTEM_PROMPT}

═══════════════════════════════════════
SYLLABUS CONTEXT — Ground Truth Modules
═══════════════════════════════════════
{syllabus_context if syllabus_context else "[No syllabus uploaded — derive headers from content]"}

═══════════════════════════════════════
RAW LECTURE TRANSCRIPT
═══════════════════════════════════════
{transcript}

═══════════════════════════════════════
FINAL INSTRUCTION
═══════════════════════════════════════
{language_line}
Apply every CORE DIRECTIVE above with full precision.
Return ONLY the JSON object. Do not add any text before or after it.
Your response must start with {{ and end with }}.
"""

    client = Groq(api_key=groq_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",   # free, 128k context window
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.2,
        max_tokens=4096,
    )

    raw = response.choices[0].message.content.strip()

    # ── Robust JSON extraction ─────────────────────────────────────────────────
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "title": "Lecture Notes",
            "summary": "Notes extracted from lecture transcript.",
            "notes": [{"module": "General", "content": raw}],
            "exam_radar": [],
            "filtered_count": 0,
            "language": "en",
        }


# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT 5 — TEXT-TO-SPEECH via gTTS (free, no API key)
# ══════════════════════════════════════════════════════════════════════════════

def notes_to_speech(notes_text: str, lang_code: str = "en") -> bytes:
    """
    Convert notes to MP3 audio using gTTS (Google Translate TTS endpoint).
    Free, no API key, just needs internet. Strips markdown before synthesis.
    """
    if not GTTS_OK or not notes_text.strip():
        return b""

    clean = notes_text
    clean = re.sub(r"#+\s*", "", clean)
    clean = re.sub(r"\*+([^*]+)\*+", r"\1", clean)
    clean = re.sub(r"`[^`]+`", "", clean)
    clean = re.sub(r"[-•]\s*", "", clean)
    clean = re.sub(r"\n{2,}", ". ", clean)
    clean = re.sub(r"\n", " ", clean).strip()
    clean = clean[:5000]

    try:
        tts = gTTS(text=clean, lang=lang_code, slow=False)
        buf = BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception as e:
        st.warning(f"TTS failed: {e}")
        return b""


def flatten_notes(result: dict) -> str:
    parts = []
    if result.get("summary"):
        parts.append(f"Summary. {result['summary']}")
    for note in result.get("notes", []):
        parts.append(f"{note.get('module', '')}. {note.get('content', '')}")
    return "\n\n".join(parts)


# ══════════════════════════════════════════════════════════════════════════════
# LANGUAGE MAP
# ══════════════════════════════════════════════════════════════════════════════

LANGUAGES = {
    "English":    ("en", "en"),
    "Spanish":    ("es", "es"),
    "French":     ("fr", "fr"),
    "German":     ("de", "de"),
    "Arabic":     ("ar", "ar"),
    "Urdu":       ("ur", "ur"),
    "Hindi":      ("hi", "hi"),
    "Portuguese": ("pt", "pt"),
    "Japanese":   ("ja", "ja"),
    "Mandarin":   ("zh-CN", "zh"),
}

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown('<div class="audora-wordmark">AUDORA</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="audora-tagline">'
        'Lecture Intelligence '
        '<span class="pill pill-green">Free</span>'
        '<span class="pill pill-blue">Windows</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Single Groq Key — does everything ─────────────────────────────────────
    st.markdown("### 🔑 Groq API Key — One Key For Everything")
    st.markdown(
        '<div class="card card-green" style="padding:0.7rem;">'
        '<p style="margin:0;font-size:0.78rem;line-height:1.7;color:#b0b8d0;">'
        '<b style="color:#4fffb0;">Free key at console.groq.com</b><br>'
        'No credit card required<br>'
        '🎙️ Transcription — 7,200 audio min/day<br>'
        '🧠 Note Generation — 14,400 req/day<br>'
        '📹 Audio <b>and</b> video files supported ✓<br>'
        '⚡ No ffmpeg needed ✓'
        '</p></div>',
        unsafe_allow_html=True,
    )
    groq_key_input = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        key="groq_key",
        help="Free from console.groq.com — handles both transcription and AI notes.",
    )
    groq_key = groq_key_input or get_env_key("GROQ_API_KEY")

    st.divider()

    # ── Language ───────────────────────────────────────────────────────────────
    st.markdown("### 🌐 Output Language")
    selected_language = st.selectbox(
        "Target language",
        options=list(LANGUAGES.keys()),
        index=0,
        label_visibility="collapsed",
    )

    st.divider()

    # ── Accessibility ──────────────────────────────────────────────────────────
    st.markdown("### ♿ Accessibility")
    enable_tts = st.checkbox(
        "Generate audio notes (gTTS)",
        value=True,
        help="Creates a free MP3 of your study notes.",
    )

    st.divider()

    # ── Component status ───────────────────────────────────────────────────────
    st.markdown("### 📦 Status")
    checks = [
        ("Groq — Transcription",    GROQ_OK,   GROQ_ERROR),
        ("Groq — Notes AI (LLaMA)", GROQ_OK,   GROQ_ERROR),
        ("Sentence-Transformers",   SBERT_OK,  SBERT_ERROR),
        ("FAISS Vector Store",      FAISS_OK,  FAISS_ERROR),
        ("PyPDF2 (PDF)",            PYPDF2_OK, PYPDF2_ERROR),
        ("gTTS (Audio)",            GTTS_OK,   GTTS_ERROR),
    ]
    for label, ok, err in checks:
        icon = "✅" if ok else "❌"
        st.markdown(
            f'<p style="font-family:\'DM Mono\',monospace;font-size:0.7rem;margin:3px 0;">'
            f'{icon} {label}</p>',
            unsafe_allow_html=True,
        )
        if not ok and err:
            st.markdown(
                f'<p style="font-size:0.63rem;color:#ff6b6b;margin:0 0 3px 14px;">'
                f'{err[:55]}…</p>',
                unsafe_allow_html=True,
            )

    st.divider()
    st.markdown(
        '<p style="font-size:0.63rem;color:#444;font-family:\'DM Mono\',monospace;">'
        'Groq Whisper · Groq LLaMA 3.3-70B · MiniLM · FAISS · gTTS</p>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN UI
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(
    '<h1 class="audora-wordmark" role="heading" aria-level="1">AUDORA'
    '<span class="pill pill-green"  style="font-size:0.55rem;">100% Free</span>'
    '<span class="pill pill-blue"   style="font-size:0.55rem;">Windows ✓</span>'
    '<span class="pill pill-orange" style="font-size:0.55rem;">1 Key Only</span>'
    '</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="audora-tagline">Syllabus-Aware Lecture Intelligence · Audio & Video · No ffmpeg · No paid subscriptions</p>',
    unsafe_allow_html=True,
)
st.divider()

# ── Missing dependencies banner ────────────────────────────────────────────────
all_core_ok = GROQ_OK and SBERT_OK and FAISS_OK
if not all_core_ok:
    missing = []
    if not GROQ_OK:  missing.append("groq")
    if not SBERT_OK: missing.append("sentence-transformers")
    if not FAISS_OK: missing.append("faiss-cpu numpy")
    st.error(
        f"**Missing packages detected. Run this once in your terminal, then restart:**\n\n"
        f"```bash\n"
        f"pip install groq sentence-transformers faiss-cpu numpy PyPDF2 gTTS streamlit python-dotenv\n"
        f"```\n\n"
        f"✅ **No ffmpeg needed.** No system-level installs required on Windows.",
        icon="🚨",
    )

# ── Key setup guide (shown when key is missing) ───────────────────────────────
if not groq_key:
    with st.expander("🔑 How to get your free Groq API key (2 minutes)", expanded=True):
        st.markdown(
            '<div class="card card-green" style="max-width:560px;">'
            '<div class="section-label">One Key — Transcription + AI Notes</div>'
            '<div class="key-step"><div class="key-num">1</div>'
            '<p style="margin:0;font-size:0.85rem;">Go to '
            '<a href="https://console.groq.com" target="_blank" style="color:#4fffb0;">'
            'console.groq.com</a></p></div>'
            '<div class="key-step"><div class="key-num">2</div>'
            '<p style="margin:0;font-size:0.85rem;">Sign up free (Google / GitHub / email)</p></div>'
            '<div class="key-step"><div class="key-num">3</div>'
            '<p style="margin:0;font-size:0.85rem;">Click <b>API Keys → Create API Key</b></p></div>'
            '<div class="key-step"><div class="key-num">4</div>'
            '<p style="margin:0;font-size:0.85rem;">Paste into the sidebar field (starts with <code>gsk_</code>)</p></div>'
            '<p style="margin:0.6rem 0 0;font-size:0.76rem;color:#7b82a0;">'
            '🎙️ 7,200 audio min/day (Whisper) &nbsp;·&nbsp; '
            '🧠 14,400 req/day (LLaMA) &nbsp;·&nbsp; No credit card'
            '</p>'
            '</div>',
            unsafe_allow_html=True,
        )

# ── File uploaders ─────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
col_left, col_right = st.columns(2, gap="large")

with col_left:
    st.markdown(
        '<div class="section-label" role="heading" aria-level="2">📄 Course Syllabus (Optional)</div>',
        unsafe_allow_html=True,
    )
    syllabus_file = st.file_uploader(
        "Upload Syllabus — PDF or TXT",
        type=["pdf", "txt"],
        key="syllabus",
        help="Processed entirely on your device. Guides the AI to use your official module names.",
    )

with col_right:
    st.markdown(
        '<div class="section-label" role="heading" aria-level="2">🎙️ Lecture Recording</div>',
        unsafe_allow_html=True,
    )
    audio_file = st.file_uploader(
        "Upload Lecture — MP3, MP4, WAV, M4A, WEBM, OGG, FLAC (max 25MB)",
        type=["mp3", "mp4", "m4a", "wav", "ogg", "flac", "webm", "mpeg", "mpga"],
        key="audio",
        help="Audio and video files both work. Sent to Groq (HTTPS). No ffmpeg needed.",
    )
    if audio_file:
        size_mb = len(audio_file.getvalue()) / (1024 * 1024)
        if size_mb > 25:
            st.warning(
                f"⚠️ File is {size_mb:.1f}MB — Groq's free limit is 25MB. "
                "Please compress to 64kbps mono MP3 before uploading.",
                icon="⚠️",
            )
        else:
            st.caption(f"✅ {audio_file.name} — {size_mb:.1f}MB, within free limit")

st.divider()

# ── Privacy note ───────────────────────────────────────────────────────────────
st.markdown(
    '<div class="card card-green" style="padding:0.7rem 1.2rem;">'
    '<p style="margin:0;font-size:0.8rem;color:#b0b8d0;">'
    '🔒 <b>Privacy:</b> Your syllabus is embedded <b>entirely on your device</b>. '
    'Audio/video is sent to Groq (HTTPS) for transcription only. '
    'The text transcript (not the audio) is sent to Groq LLaMA for note generation. '
    'Nothing is stored or used for training.'
    '</p></div>',
    unsafe_allow_html=True,
)

# ── Run button ─────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
_, btn_col, _ = st.columns([2, 3, 2])
with btn_col:
    keys_ready = bool(groq_key)
    file_ready = bool(audio_file)
    can_run    = keys_ready and file_ready and all_core_ok
    run_button = st.button(
        "⚡ Generate Notes — Free",
        disabled=not can_run,
        use_container_width=True,
        help="Add your free Groq API key and upload an audio/video file to begin.",
    )

if not keys_ready:
    st.info("👈 Add your free **Groq** API key in the sidebar to begin.", icon="🔑")
elif not file_ready:
    st.info("👆 Upload a lecture recording (audio or video) to get started.", icon="🎙️")

# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE EXECUTION
# ══════════════════════════════════════════════════════════════════════════════

if run_button and can_run:

    result, transcript = {}, ""
    progress = st.progress(0, text="Starting pipeline…")

    # ── STEP 1: Syllabus → local FAISS index ──────────────────────────────────
    vector_store = None
    if syllabus_file:
        progress.progress(5, text="📚 Indexing syllabus locally…")
        try:
            raw = syllabus_file.read()
            text = (
                extract_pdf_text(raw)
                if syllabus_file.name.lower().endswith(".pdf")
                else raw.decode("utf-8", errors="replace")
            )
            if text.strip():
                vector_store = build_vector_store(text)
                if vector_store:
                    st.toast(f"✅ Syllabus indexed — {len(vector_store.chunks)} chunks", icon="📚")
                else:
                    st.warning("Syllabus indexing skipped (missing sentence-transformers or faiss-cpu).")
            else:
                st.warning("Could not extract text from syllabus — check the PDF is not a scanned image.")
        except Exception as e:
            st.warning(f"Syllabus error: {e} — continuing without syllabus context.")
    else:
        st.info("No syllabus uploaded — notes will use content-based headers.", icon="ℹ️")

    # ── STEP 2: Audio/Video → transcript via Groq Whisper ─────────────────────
    progress.progress(15, text="🎙️ Transcribing with Groq Whisper (no ffmpeg)…")
    try:
        audio_bytes = audio_file.getvalue()
        with st.spinner("Sending to Groq for transcription… (usually 10–30 seconds)"):
            transcript = transcribe_with_groq(audio_bytes, audio_file.name, groq_key)

        if not transcript:
            st.error("Transcription returned empty. Check your file has audible speech.")
            st.stop()

        st.toast(f"✅ Transcript ready — {len(transcript.split()):,} words", icon="🎙️")

    except Exception as e:
        st.error(f"Transcription failed: {e}")
        with st.expander("🔍 Debug details"):
            st.code(traceback.format_exc())
        st.stop()

    # ── STEP 3: Retrieve syllabus context ─────────────────────────────────────
    progress.progress(50, text="🔍 Matching transcript to syllabus modules…")
    syllabus_context = get_syllabus_context(vector_store, transcript[:4000])

    # ── STEP 4: Groq LLaMA note generation ────────────────────────────────────
    progress.progress(60, text="🧠 Generating structured notes with Groq LLaMA…")
    try:
        lang_code, tts_lang = LANGUAGES[selected_language]
        result = generate_notes_with_groq_llm(
            transcript=transcript,
            syllabus_context=syllabus_context,
            groq_key=groq_key,
            target_language=selected_language,
        )
        st.toast("✅ Notes generated", icon="🧠")
    except Exception as e:
        st.error(f"Note generation failed: {e}")
        with st.expander("🔍 Debug details"):
            st.code(traceback.format_exc())
        st.stop()

    # ── STEP 5: TTS synthesis ──────────────────────────────────────────────────
    audio_out = b""
    if enable_tts and GTTS_OK:
        progress.progress(88, text="🔊 Synthesising audio notes…")
        audio_out = notes_to_speech(flatten_notes(result), lang_code=tts_lang)
        if audio_out:
            st.toast("✅ Audio notes ready", icon="🔊")

    progress.progress(100, text="✅ All done!")

    # ══════════════════════════════════════════════════════════════════════════
    # RESULTS DISPLAY
    # ══════════════════════════════════════════════════════════════════════════

    st.divider()

    title      = result.get("title", "Lecture Notes")
    summary    = result.get("summary", "")
    notes      = result.get("notes", [])
    exam_hints = result.get("exam_radar", [])
    filtered_n = result.get("filtered_count", 0)

    st.markdown(
        f'<h2 style="font-family:\'Syne\',sans-serif;font-size:1.75rem;'
        f'font-weight:800;color:#e8eaf2;" role="heading" aria-level="2">{title}</h2>',
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Language",         selected_language)
    m2.metric("Noise Removed",    filtered_n)
    m3.metric("Exam Hints",       len(exam_hints))
    m4.metric("Transcript Words", f"{len(transcript.split()):,}")

    if summary:
        st.markdown(
            f'<div class="card card-green" role="region" aria-label="Lecture summary">'
            f'<div class="section-label">Executive Summary</div>'
            f'<p style="margin:0;line-height:1.75;">{summary}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    notes_col, radar_col = st.columns([3, 2], gap="large")

    with notes_col:
        st.markdown(
            '<div class="section-label" role="heading" aria-level="3">📝 Clean Study Notes</div>',
            unsafe_allow_html=True,
        )
        if notes:
            for note in notes:
                mod  = note.get("module", "General")
                body = note.get("content", "")
                st.markdown(
                    f'<div class="card" role="region" aria-label="Notes: {mod}">'
                    f'<div class="section-label">{mod}</div>'
                    f'<div class="notes-body">{body}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No structured notes were returned.")

        if audio_out:
            st.divider()
            st.markdown(
                '<div class="section-label" role="heading" aria-level="3">'
                '🔊 Audio Notes — Accessibility</div>',
                unsafe_allow_html=True,
            )
            st.caption("Listen to your notes — ideal for auditory learners and accessibility.")
            st.audio(audio_out, format="audio/mp3")

    with radar_col:
        st.markdown(
            '<div class="section-label" role="heading" aria-level="3">🎯 Exam Radar</div>',
            unsafe_allow_html=True,
        )
        if exam_hints:
            for h in exam_hints:
                urgency = h.get("urgency", "MEDIUM").upper()
                cls     = "rbadge-high" if urgency == "HIGH" else "rbadge-med"
                mod     = h.get("module", "")
                hint    = h.get("hint", "")
                reason  = h.get("reason", "")
                st.markdown(
                    f'<div class="card card-red" role="alert" aria-label="Exam hint: {hint}">'
                    f'<span class="rbadge {cls}">{urgency}</span>'
                    f'<span class="rbadge rbadge-mod">{mod}</span>'
                    f'<p style="margin:0.55rem 0 0.25rem;font-weight:500;font-size:0.95rem;">{hint}</p>'
                    f'<p style="font-size:0.78rem;color:#7b82a0;margin:0;">{reason}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="card" style="text-align:center;color:#7b82a0;padding:2rem;">'
                '<p style="font-size:1.8rem;margin-bottom:0.5rem;">✅</p>'
                '<p style="margin:0;font-size:0.9rem;">No exam hints detected.</p>'
                '</div>',
                unsafe_allow_html=True,
            )

        st.divider()
        with st.expander("📜 Raw Transcript", expanded=False):
            preview = transcript[:3000] + ("…" if len(transcript) > 3000 else "")
            st.markdown(
                f'<div style="font-family:\'DM Mono\',monospace;font-size:0.78rem;'
                f'color:#7b82a0;line-height:1.7;white-space:pre-wrap;">{preview}</div>',
                unsafe_allow_html=True,
            )

    # ── Downloads ──────────────────────────────────────────────────────────────
    st.divider()
    dl1, dl2, dl3, _ = st.columns([2, 2, 2, 1])

    md = f"# {title}\n\n**Summary:** {summary}\n\n"
    for n in notes:
        md += f"## {n.get('module','')}\n\n{n.get('content','')}\n\n"
    if exam_hints:
        md += "## 🎯 Exam Radar\n\n"
        for h in exam_hints:
            md += f"- **[{h.get('urgency')}]** {h.get('hint')}  *(Module: {h.get('module')})*\n"

    safe_title = re.sub(r"[^a-zA-Z0-9_]", "_", title[:28])

    with dl1:
        st.download_button(
            "⬇️ Markdown Notes",
            data=md,
            file_name=f"audora_{safe_title}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with dl2:
        st.download_button(
            "⬇️ Raw JSON",
            data=json.dumps(result, indent=2, ensure_ascii=False),
            file_name="audora_result.json",
            mime="application/json",
            use_container_width=True,
        )
    with dl3:
        st.download_button(
            "⬇️ Transcript",
            data=transcript,
            file_name=f"transcript_{safe_title}.txt",
            mime="text/plain",
            use_container_width=True,
        )

# ── Empty state ────────────────────────────────────────────────────────────────
elif not run_button:
    st.markdown(
        '<div class="card" style="text-align:center;padding:2.5rem 2rem;">'
        '<p style="font-size:2.8rem;margin-bottom:0.8rem;">🎓</p>'
        '<h3 style="font-family:\'Syne\',sans-serif;font-weight:800;'
        'color:#e8eaf2;margin-bottom:0.6rem;">Built for students on a budget</h3>'
        '<p style="color:#7b82a0;max-width:560px;margin:0 auto;line-height:1.75;font-size:0.92rem;">'
        'No Gemini. No OpenAI. No ffmpeg. No paid subscriptions.<br>'
        'Just <b>one free Groq key</b> — handles both audio/video transcription '
        'and AI-powered note generation with LLaMA 3.3-70B.<br>'
        'Upload your lecture MP3, MP4, or any audio/video file and Audora handles the rest — '
        'transcription, syllabus matching, noise filtering, and exam detection.'
        '</p>'
        '<p style="margin-top:1.2rem;font-size:0.8rem;color:#555;">'
        'Works on Windows · 8GB RAM · No system installs · One API key'
        '</p>'
        '</div>',
        unsafe_allow_html=True,
    )