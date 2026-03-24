"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                            AUDORA MVP                                        ║
║              Syllabus-Aware AI Lecture Intelligence System                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

ARCHITECTURE OVERVIEW
─────────────────────
1. INGEST
   • Syllabus PDF  → PyPDF2 text extraction → RecursiveCharacterTextSplitter
     → OpenAIEmbeddings → FAISS vectorstore (in-memory)
   • Lecture MP3   → OpenAI Whisper API → raw transcript (timestamped)

2. NOISE GATE
   • The raw transcript is passed through a semantic filter prompt that
     identifies and strips non-academic segments (greetings, roll-call,
     disciplinary remarks, jokes, admin notices) before any further
     processing.

3. SYLLABUS-AWARE RAG (Retrieval-Augmented Generation)
   • Each transcript sentence/chunk is embedded and queried against the
     FAISS syllabus store.  The top-k syllabus chunks become the
     "grounding context" injected into the LLM prompt, ensuring that
     generated headers mirror official module names from the syllabus.

4. LLM REASONING  (GPT-4o / Claude 3.5)
   • System prompt (below) instructs the model to:
       a) Map content to syllabus modules
       b) Remove fluff
       c) Return structured JSON with "notes" and "exam_radar"

5. EXAM RADAR
   • During LLM processing, urgency signals (mid-term, final, paper,
     important, remember, exam, quiz, assignment) are flagged and
     returned in the exam_radar JSON array.

6. OUTPUT
   • Structured markdown notes rendered in Streamlit
   • Exam Radar alert cards
   • gTTS audio synthesis of the notes → st.audio player
   • Optional translation via LLM before TTS
"""

import os
import json
import tempfile
import textwrap
import re
import traceback
from pathlib import Path
from io import BytesIO

import streamlit as st

# Load local .env (useful for OPENAI_API_KEY during development).
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

# ── optional imports with graceful error messages ──────────────────────────────
try:
    import openai
    OPENAI_IMPORT_ERROR = None
except ImportError as e:
    openai = None
    OPENAI_IMPORT_ERROR = str(e)

try:
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    from langchain_community.vectorstores import FAISS
    try:
        # Newer LangChain splits text splitters into a dedicated package.
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        # Older LangChain versions keep splitters under `langchain.text_splitter`.
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    try:
        # Newer LangChain versions expose messages via langchain_core.
        from langchain_core.messages import SystemMessage, HumanMessage
    except ImportError:
        # Backwards-compatible fallback.
        from langchain.schema import SystemMessage, HumanMessage

    LANGCHAIN_OK = True
    LANGCHAIN_IMPORT_ERROR = None
except ImportError as e:
    LANGCHAIN_OK = False
    LANGCHAIN_IMPORT_ERROR = str(e)

try:
    import PyPDF2
    PYPDF2_OK = True
except ImportError:
    PYPDF2_OK = False

try:
    from gtts import gTTS
    GTTS_OK = True
except ImportError:
    GTTS_OK = False

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & STYLING
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Audora — Syllabus-Aware Lecture Intelligence",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# High-contrast, accessible dark theme with strong typography
st.markdown("""
<style>
  /* ── Imports ── */
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@400;500&family=Inter:wght@300;400;500&display=swap');

  /* ── Root palette ── */
  :root {
    --bg:        #0d0f14;
    --surface:   #161a23;
    --border:    #252b3a;
    --accent:    #4fffb0;   /* electric mint — high contrast on dark */
    --accent2:   #ff6b6b;   /* exam radar red */
    --accent3:   #ffd166;   /* warning amber */
    --text:      #e8eaf2;
    --muted:     #7b82a0;
    --radius:    12px;
  }

  /* ── Global reset ── */
  html, body, [class*="css"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif;
  }

  /* ── App container ── */
  .main .block-container { padding: 2rem 3rem; max-width: 1280px; }

  /* ── Hero wordmark ── */
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
    margin-bottom: 0;
  }
  .audora-tagline {
    font-family: 'DM Mono', monospace;
    font-size: 0.85rem;
    color: var(--muted);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 0.25rem;
  }

  /* ── Cards ── */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 1.25rem;
  }
  .card-accent { border-left: 4px solid var(--accent); }
  .card-danger  { border-left: 4px solid var(--accent2); }
  .card-warning { border-left: 4px solid var(--accent3); }

  /* ── Section headers ── */
  .section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 0.75rem;
  }

  /* ── Exam Radar badge ── */
  .radar-badge {
    display: inline-block;
    background: rgba(255,107,107,0.15);
    border: 1px solid var(--accent2);
    color: var(--accent2);
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-family: 'DM Mono', monospace;
    font-weight: 500;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-right: 0.5rem;
    margin-bottom: 0.35rem;
  }
  .radar-high  { border-color: #ff4444; color: #ff4444; background: rgba(255,68,68,0.12); }
  .radar-med   { border-color: var(--accent3); color: var(--accent3); background: rgba(255,209,102,0.10); }

  /* ── Note content ── */
  .notes-body {
    font-family: 'Inter', sans-serif;
    font-size: 1rem;
    line-height: 1.8;
    color: var(--text);
  }
  .notes-body h2 {
    font-family: 'Syne', sans-serif;
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--accent);
    margin-top: 1.75rem;
    margin-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.4rem;
  }
  .notes-body h3 {
    font-family: 'Syne', sans-serif;
    font-size: 1.05rem;
    color: #7ee8c8;
    margin-top: 1.25rem;
  }
  .notes-body ul { padding-left: 1.4rem; }
  .notes-body li { margin-bottom: 0.35rem; }
  .notes-body strong { color: #ffd166; }

  /* ── Upload zones ── */
  [data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 2px dashed var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1rem !important;
  }
  [data-testid="stFileUploader"]:hover {
    border-color: var(--accent) !important;
  }

  /* ── Buttons ── */
  .stButton > button {
    background: var(--accent) !important;
    color: #0d0f14 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 2rem !important;
    width: 100%;
    letter-spacing: 0.5px;
    transition: opacity 0.2s;
  }
  .stButton > button:hover { opacity: 0.85 !important; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
  }

  /* ── Selectbox / inputs ── */
  .stSelectbox > div > div, .stTextInput > div > div > input {
    background: var(--bg) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
    border-radius: 8px !important;
  }

  /* ── Progress / spinner ── */
  .stProgress > div > div { background: var(--accent) !important; }
  .stSpinner > div { border-top-color: var(--accent) !important; }

  /* ── Divider ── */
  hr { border-color: var(--border) !important; }

  /* ── Accessibility: focus ring ── */
  *:focus-visible { outline: 2px solid var(--accent) !important; outline-offset: 2px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# THE "BRAIN" — SYSTEM PROMPT
# ══════════════════════════════════════════════════════════════════════════════

AUDORA_SYSTEM_PROMPT = """
You are Audora, an elite academic note-taking AI. Your role is to transform a
raw lecture transcript into structured, high-signal study notes — guided
exclusively by the official course syllabus provided as context.

═══════════════════════════════════════════════════════
CORE DIRECTIVES
═══════════════════════════════════════════════════════

1. NOISE GATE — DISCARD completely (do not mention, summarise, or reference):
   • Greetings, farewells, small-talk ("good morning", "see you next week")
   • Administrative announcements (room changes, registration deadlines)
   • Attendance & roll-call ("anyone absent?", "sign the sheet")
   • Disciplinary remarks ("put your phone away", "no talking")
   • Jokes, tangents, and personal anecdotes unrelated to course content
   • Repetition/filler ("um", "uh", "you know", "basically")

2. SYLLABUS MAPPING — Structure notes under official module/topic headers
   drawn directly from the SYLLABUS CONTEXT provided. If a lecture segment
   does not map to any syllabus topic, use the closest match and note it with
   "(Extended Coverage)". Never invent module names.

3. EXAM RADAR — Detect urgency signals in the transcript. Trigger phrases
   include (but are not limited to): "mid-term", "final exam", "quiz",
   "assignment", "paper", "project", "will be tested", "remember this",
   "important", "key concept", "this comes up", "you need to know",
   "exam question", "marks", "graded". For each detected signal, record the
   hint verbatim (cleaned of filler) plus its urgency level (HIGH or MEDIUM).

4. MULTILINGUAL OUTPUT — If a target language is specified, write ALL notes
   and summaries in that language. Retain original technical terminology in
   English with a parenthetical translation.

═══════════════════════════════════════════════════════
OUTPUT FORMAT — Return ONLY valid JSON, no markdown fences:
═══════════════════════════════════════════════════════

{
  "title": "<Lecture title inferred from content>",
  "summary": "<2-3 sentence executive summary of the lecture>",
  "notes": [
    {
      "module": "<Exact syllabus module name>",
      "content": "<Well-structured markdown: use ## headings, bullet points, bold for key terms, and code blocks for formulas/algorithms>"
    }
  ],
  "exam_radar": [
    {
      "hint": "<Cleaned verbatim exam hint from lecturer>",
      "module": "<Relevant module name>",
      "urgency": "HIGH | MEDIUM",
      "reason": "<Why this is flagged — what was said>"
    }
  ],
  "filtered_count": <integer — number of noise segments removed>,
  "language": "<ISO 639-1 code of output language>"
}
"""

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_api_key() -> str:
    """Retrieve OpenAI key from env or Streamlit secrets."""
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        try:
            key = (st.secrets.get("OPENAI_API_KEY", "") or "").strip()
        except Exception:
            pass
    return key


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """
    Extract plain text from a PDF file.
    Falls back to a page-by-page extraction strategy.
    """
    if not PYPDF2_OK:
        st.error("PyPDF2 not installed. Run: pip install PyPDF2")
        return ""
    reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)


def build_syllabus_vectorstore(syllabus_text: str, api_key: str):
    """
    SYLLABUS VECTORIZATION PIPELINE
    ────────────────────────────────
    1. Split the syllabus into overlapping chunks so that topic boundaries
       are captured even when a topic spans paragraph breaks.
    2. Embed each chunk with OpenAI's text-embedding model.
    3. Store in FAISS — a fast in-memory approximate-nearest-neighbor index.

    This store acts as the "Ground Truth" during LLM prompting:
    we retrieve the top-k most relevant syllabus chunks for each lecture
    segment, injecting them as grounding context so the LLM aligns its
    headers with official module names rather than hallucinating new ones.
    """
    if not LANGCHAIN_OK:
        return None

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,       # ~150 words — enough for one syllabus topic
        chunk_overlap=100,    # overlap preserves topic name at chunk edges
        separators=["\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_text(syllabus_text)

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=api_key,
    )
    vectorstore = FAISS.from_texts(chunks, embeddings)
    return vectorstore


def retrieve_syllabus_context(vectorstore, query: str, k: int = 5) -> str:
    """
    SYLLABUS MATCHING LOGIC
    ────────────────────────
    Given a transcript chunk (the query), find the top-k syllabus passages
    that are semantically closest.  These passages are injected into the
    LLM prompt as the authoritative source of module names.

    Why top-k=5?  A lecture segment can legitimately span multiple syllabus
    topics (e.g., a transition lecture), so we allow up to 5 anchors.
    """
    if vectorstore is None:
        return ""
    docs = vectorstore.similarity_search(query, k=k)
    return "\n---\n".join([d.page_content for d in docs])


def transcribe_audio(audio_bytes: bytes, api_key: str, filename: str = "lecture.mp3") -> str:
    """
    SPEECH-TO-TEXT via OpenAI Whisper API
    ──────────────────────────────────────
    Whisper handles accents, technical jargon, and mixed-language audio well.
    We write to a temp file because the API requires a file-like object with
    a known extension.
    Returns the full raw transcript as a single string.
    """
    if openai is None:
        st.error("openai package not installed. Run: pip install openai")
        return ""

    api_key = (api_key or "").strip()
    if not api_key:
        raise ValueError(
            "OpenAI API key is empty. Set `OPENAI_API_KEY` or enter your key in the sidebar."
        )

    client = openai.OpenAI(api_key=api_key)

    suffix = Path(filename).suffix or ".mp3"
    tmp_path = None
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",  # plain text — fastest for MVP
            )
        return response
    except Exception as e:
        # Surface the underlying OpenAI exception (network vs auth vs status).
        detail_parts = [f"{type(e).__name__}: {e}"]
        detail_parts.append(f"API key length: {len(api_key)}")
        resp = getattr(e, "response", None)
        if resp is not None:
            try:
                detail_parts.append(f"Response status: {getattr(resp, 'status_code', 'unknown')}")
            except Exception:
                pass
            try:
                body = getattr(resp, "text", None) or getattr(resp, "content", None)
                if body:
                    detail_parts.append(f"Response body: {body}")
            except Exception:
                pass
        if getattr(e, "__cause__", None) is not None:
            detail_parts.append(f"Cause: {repr(e.__cause__)}")
        raise RuntimeError(
            "Whisper transcription call failed.\n" + "\n".join(detail_parts)
        ) from e
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def run_audora_chain(
    transcript: str,
    vectorstore,
    api_key: str,
    target_language: str = "English",
) -> dict:
    """
    CORE RAG + LLM PIPELINE
    ────────────────────────
    1. Retrieve the most relevant syllabus context for the full transcript.
       (For longer lectures we'd chunk the transcript and call per-chunk,
        but for MVP we use the full transcript with a broad syllabus query.)
    2. Build the final prompt: system instructions + syllabus context + transcript.
    3. Call GPT-4o (or compatible model) and parse the JSON response.
    """
    if not LANGCHAIN_OK:
        st.error("LangChain not installed. Run: pip install langchain langchain-openai langchain-community faiss-cpu")
        return {}

    # Retrieve relevant syllabus anchors using the full transcript as query
    # In production: chunk transcript → retrieve per-chunk → merge
    syllabus_context = retrieve_syllabus_context(vectorstore, transcript[:4000], k=8)

    language_instruction = (
        f"Write all notes and summaries in {target_language}. "
        "Keep technical terms in English with translations in parentheses."
        if target_language.lower() != "english"
        else ""
    )

    human_message = f"""
═══════════════════════════════════
SYLLABUS CONTEXT (Ground Truth)
═══════════════════════════════════
{syllabus_context if syllabus_context else "[No syllabus provided — use content-based headers]"}

═══════════════════════════════════
RAW LECTURE TRANSCRIPT
═══════════════════════════════════
{transcript}

═══════════════════════════════════
INSTRUCTIONS
═══════════════════════════════════
{language_instruction}
Apply all CORE DIRECTIVES. Return only the JSON object described in your system prompt.
""".strip()

    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.2,         # low temp → factual, consistent structure
        max_tokens=4096,
        openai_api_key=api_key,
    )

    messages = [
        SystemMessage(content=AUDORA_SYSTEM_PROMPT),
        HumanMessage(content=human_message),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()

    # Strip any accidental markdown fences the model might add
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Graceful degradation: return raw text as a note
        return {
            "title": "Lecture Notes",
            "summary": "",
            "notes": [{"module": "General", "content": raw}],
            "exam_radar": [],
            "filtered_count": 0,
            "language": "en",
        }


def notes_to_speech(notes_text: str, lang_code: str = "en") -> bytes:
    """
    TEXT-TO-SPEECH ACCESSIBILITY LAYER
    ────────────────────────────────────
    Converts the clean notes into an MP3 audio stream using gTTS.
    Strips markdown symbols before synthesis so the audio is clean.
    Returns raw MP3 bytes for st.audio().
    """
    if not GTTS_OK:
        return b""

    # Strip markdown formatting for clean TTS
    clean = re.sub(r"#+\s*", "", notes_text)      # remove headers
    clean = re.sub(r"\*+([^*]+)\*+", r"\1", clean)  # remove bold/italic
    clean = re.sub(r"`[^`]+`", "", clean)           # remove inline code
    clean = re.sub(r"[-•]\s*", "", clean)           # remove bullets
    clean = re.sub(r"\n{2,}", ". ", clean)          # double newlines → pause
    clean = re.sub(r"\n", " ", clean).strip()

    # Truncate for MVP (gTTS has no hard limit but very long text is slow)
    clean = clean[:5000]

    tts = gTTS(text=clean, lang=lang_code, slow=False)
    buf = BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()


def flatten_notes_to_text(result: dict) -> str:
    """Flatten the structured JSON notes into a single readable string for TTS."""
    parts = []
    if result.get("summary"):
        parts.append(f"Summary: {result['summary']}")
    for note in result.get("notes", []):
        parts.append(f"\n\n{note['module']}.\n{note['content']}")
    return "\n".join(parts)


# Language map: display name → (ISO 639-1, gTTS lang code)
LANGUAGES = {
    "English":    ("en", "en"),
    "Spanish":    ("es", "es"),
    "French":     ("fr", "fr"),
    "German":     ("de", "de"),
    "Arabic":     ("ar", "ar"),
    "Urdu":       ("ur", "ur"),
    "Hindi":      ("hi", "hi"),
    "Mandarin":   ("zh", "zh"),
    "Portuguese": ("pt", "pt"),
    "Japanese":   ("ja", "ja"),
}

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown('<div class="audora-wordmark">AUDORA</div>', unsafe_allow_html=True)
    st.markdown('<div class="audora-tagline">Lecture Intelligence</div>', unsafe_allow_html=True)
    st.divider()

    # API Key input — secure, never logged
    st.markdown("### ⚙️ Configuration")
    api_key_input = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-...",
        help="Your key is used only for this session and never stored.",
        key="api_key",
    )
    # Merge env key with UI input
    api_key = api_key_input or get_api_key()

    st.divider()

    # Language selector
    st.markdown("### 🌐 Output Language")
    selected_language = st.selectbox(
        "Target language for notes",
        options=list(LANGUAGES.keys()),
        index=0,
        help="Notes will be translated into this language. Technical terms remain in English.",
        label_visibility="collapsed",
    )

    st.divider()

    # Accessibility options
    st.markdown("### ♿ Accessibility")
    enable_tts = st.checkbox(
        "Generate audio version of notes",
        value=True,
        help="Creates an MP3 of the clean notes for screen reader / listening use.",
    )

    st.divider()
    st.markdown(
        '<p style="font-size:0.7rem;color:#555;font-family:\'DM Mono\',monospace;">'
        'Audora v0.1 MVP · GPT-4o + Whisper + FAISS</p>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN INTERFACE
# ══════════════════════════════════════════════════════════════════════════════

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown(
    '<h1 class="audora-wordmark" role="heading" aria-level="1">AUDORA</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="audora-tagline">Syllabus-Aware Lecture Intelligence · Turn audio into A+ notes</p>',
    unsafe_allow_html=True,
)
st.divider()

# ── Dependency check banner ───────────────────────────────────────────────────
missing = []
if not LANGCHAIN_OK: missing.append("`langchain langchain-openai langchain-community faiss-cpu`")
if not PYPDF2_OK:    missing.append("`PyPDF2`")
if not GTTS_OK:      missing.append("`gTTS`")
if openai is None:   missing.append("`openai`")

if missing:
    extra = []
    if not LANGCHAIN_OK and LANGCHAIN_IMPORT_ERROR:
        extra.append(f"LangChain import error: {LANGCHAIN_IMPORT_ERROR}")
    if openai is None and OPENAI_IMPORT_ERROR:
        extra.append(f"openai import error: {OPENAI_IMPORT_ERROR}")
    warning_text = (
        "**Missing dependencies.** Install them and restart:\n\n"
        "```bash\npip install openai langchain langchain-openai langchain-community "
        "faiss-cpu PyPDF2 gTTS streamlit\n```"
    )
    if extra:
        warning_text += "\n\nImport details:\n" + "\n".join(extra)
    st.warning(warning_text, icon="⚠️")

# ── Upload columns ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2, gap="large")

with col_left:
    st.markdown(
        '<div class="section-label" role="heading" aria-level="2">📄 Course Syllabus</div>',
        unsafe_allow_html=True,
    )
    syllabus_file = st.file_uploader(
        "Upload Syllabus (PDF or TXT)",
        type=["pdf", "txt"],
        key="syllabus",
        label_visibility="visible",
        help="The syllabus is vectorized and used as ground truth for note structure.",
    )

with col_right:
    st.markdown(
        '<div class="section-label" role="heading" aria-level="2">🎙️ Lecture Recording</div>',
        unsafe_allow_html=True,
    )
    audio_file = st.file_uploader(
        "Upload Lecture (MP3 or MP4)",
        type=["mp3", "mp4", "m4a", "wav"],
        key="audio",
        label_visibility="visible",
        help="Audio is transcribed with OpenAI Whisper. Mixed-language recordings are supported.",
    )

st.divider()

# ── Process button ─────────────────────────────────────────────────────────────
_, btn_col, _ = st.columns([2, 3, 2])
with btn_col:
    run_button = st.button(
        "⚡ Generate Notes",
        disabled=not (audio_file and api_key),
        help="Upload a lecture recording and provide your API key to begin.",
        use_container_width=True,
    )

if not api_key:
    st.info("👈 Enter your OpenAI API key in the sidebar to get started.", icon="🔑")

# ══════════════════════════════════════════════════════════════════════════════
# PROCESSING PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

if run_button and audio_file and api_key:

    result = {}
    progress = st.progress(0, text="Initialising…")

    # ── STEP 1: Syllabus vectorization ─────────────────────────────────────
    vectorstore = None
    if syllabus_file:
        progress.progress(10, text="📚 Vectorizing syllabus…")
        try:
            raw_bytes = syllabus_file.read()
            if syllabus_file.name.endswith(".pdf"):
                syllabus_text = extract_pdf_text(raw_bytes)
            else:
                syllabus_text = raw_bytes.decode("utf-8", errors="replace")

            if syllabus_text.strip():
                vectorstore = build_syllabus_vectorstore(syllabus_text, api_key)
                st.toast("✅ Syllabus vectorized successfully", icon="📚")
            else:
                st.warning("Could not extract text from syllabus — proceeding without it.")
        except Exception as e:
            st.warning(f"Syllabus processing error: {e}. Continuing without syllabus context.")
    else:
        st.info("No syllabus uploaded — notes will use content-based headers.", icon="ℹ️")

    # ── STEP 2: Audio transcription ─────────────────────────────────────────
    progress.progress(30, text="🎙️ Transcribing lecture with Whisper…")
    try:
        audio_bytes = audio_file.read()
        transcript = transcribe_audio(audio_bytes, api_key, filename=audio_file.name)
        if not transcript:
            st.error("Transcription returned empty. Check your API key and audio file.")
            st.stop()
        st.toast("✅ Transcription complete", icon="🎙️")
    except Exception as e:
        st.error(f"Transcription failed ({type(e).__name__}): {e}")
        with st.expander("Transcription debug details"):
            st.code(traceback.format_exc())
        st.stop()

    # ── STEP 3: LLM reasoning + note generation ─────────────────────────────
    progress.progress(55, text="🧠 Analysing lecture & generating notes…")
    try:
        lang_code, tts_code = LANGUAGES[selected_language]
        result = run_audora_chain(
            transcript=transcript,
            vectorstore=vectorstore,
            api_key=api_key,
            target_language=selected_language,
        )
        st.toast("✅ Notes generated", icon="🧠")
    except Exception as e:
        st.error(f"LLM processing failed: {e}")
        st.stop()

    # ── STEP 4: TTS synthesis ────────────────────────────────────────────────
    audio_data = b""
    if enable_tts and GTTS_OK and result:
        progress.progress(80, text="🔊 Synthesising audio notes…")
        try:
            notes_text = flatten_notes_to_text(result)
            audio_data = notes_to_speech(notes_text, lang_code=tts_code)
            st.toast("✅ Audio notes ready", icon="🔊")
        except Exception as e:
            st.warning(f"TTS synthesis failed: {e}. Text notes still available.")

    progress.progress(100, text="✅ Done!")

    # ══════════════════════════════════════════════════════════════════════════
    # RESULTS DISPLAY
    # ══════════════════════════════════════════════════════════════════════════

    st.divider()

    # ── Lecture title & summary ───────────────────────────────────────────────
    title = result.get("title", "Lecture Notes")
    summary = result.get("summary", "")
    filtered_count = result.get("filtered_count", 0)

    st.markdown(
        f'<h2 style="font-family:\'Syne\',sans-serif;font-size:1.8rem;font-weight:800;'
        f'color:#e8eaf2;" role="heading" aria-level="2">{title}</h2>',
        unsafe_allow_html=True,
    )

    meta_cols = st.columns(3)
    meta_cols[0].metric("Language", selected_language)
    meta_cols[1].metric("Noise Segments Removed", filtered_count)
    meta_cols[2].metric("Exam Hints Found", len(result.get("exam_radar", [])))

    if summary:
        st.markdown(
            f'<div class="card card-accent" role="region" aria-label="Lecture summary">'
            f'<div class="section-label">Executive Summary</div>'
            f'<p style="margin:0;line-height:1.7">{summary}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Main layout: notes + radar ─────────────────────────────────────────────
    notes_col, radar_col = st.columns([3, 2], gap="large")

    # ── CLEAN NOTES ────────────────────────────────────────────────────────────
    with notes_col:
        st.markdown(
            '<div class="section-label" role="heading" aria-level="3">📝 Clean Study Notes</div>',
            unsafe_allow_html=True,
        )

        notes = result.get("notes", [])
        if notes:
            for note in notes:
                module_name = note.get("module", "General")
                content = note.get("content", "")
                st.markdown(
                    f'<div class="card" role="region" aria-label="Notes for {module_name}">'
                    f'<div class="section-label">{module_name}</div>'
                    f'<div class="notes-body">{content}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No structured notes were generated.")

        # ── Audio notes player ─────────────────────────────────────────────
        if audio_data:
            st.divider()
            st.markdown(
                '<div class="section-label" role="heading" aria-level="3">🔊 Audio Notes (Accessibility)</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<p style="font-size:0.85rem;color:#7b82a0;margin-bottom:0.75rem;">'
                'Listen to your study notes — optimised for screen readers and auditory learners.</p>',
                unsafe_allow_html=True,
            )
            st.audio(audio_data, format="audio/mp3")

    # ── EXAM RADAR ─────────────────────────────────────────────────────────────
    with radar_col:
        st.markdown(
            '<div class="section-label" role="heading" aria-level="3">🎯 Exam Radar</div>',
            unsafe_allow_html=True,
        )

        exam_hints = result.get("exam_radar", [])
        if exam_hints:
            for hint in exam_hints:
                urgency = hint.get("urgency", "MEDIUM").upper()
                badge_class = "radar-high" if urgency == "HIGH" else "radar-med"
                module = hint.get("module", "")
                hint_text = hint.get("hint", "")
                reason = hint.get("reason", "")

                st.markdown(
                    f'<div class="card card-danger" role="alert" aria-label="Exam hint: {hint_text}">'
                    f'<span class="radar-badge {badge_class}">{urgency}</span>'
                    f'<span class="radar-badge" style="color:#7b82a0;border-color:#252b3a">{module}</span>'
                    f'<p style="margin:0.6rem 0 0.3rem;font-weight:500">{hint_text}</p>'
                    f'<p style="font-size:0.8rem;color:#7b82a0;margin:0">{reason}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="card" style="text-align:center;color:#7b82a0">'
                '<p style="font-size:2rem;margin-bottom:0.5rem">✅</p>'
                '<p style="margin:0">No specific exam hints detected in this lecture.</p>'
                '</div>',
                unsafe_allow_html=True,
            )

        # ── Raw transcript expander ────────────────────────────────────────
        st.divider()
        with st.expander("📜 View Raw Transcript", expanded=False):
            st.markdown(
                f'<div style="font-family:\'DM Mono\',monospace;font-size:0.8rem;'
                f'color:#7b82a0;line-height:1.7;white-space:pre-wrap;">'
                f'{transcript[:3000]}{"…" if len(transcript) > 3000 else ""}'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Download notes as markdown ──────────────────────────────────────────
    st.divider()
    dl_col1, dl_col2, _ = st.columns([2, 2, 3])

    all_notes_md = f"# {title}\n\n**Summary:** {summary}\n\n"
    for note in result.get("notes", []):
        all_notes_md += f"## {note['module']}\n\n{note['content']}\n\n"
    if exam_hints:
        all_notes_md += "## 🎯 Exam Radar\n\n"
        for h in exam_hints:
            all_notes_md += f"- **[{h.get('urgency')}]** {h.get('hint')} *(Module: {h.get('module')})*\n"

    with dl_col1:
        st.download_button(
            label="⬇️ Download Notes (Markdown)",
            data=all_notes_md,
            file_name=f"audora_{title[:30].replace(' ','_')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with dl_col2:
        st.download_button(
            label="⬇️ Download Raw JSON",
            data=json.dumps(result, indent=2, ensure_ascii=False),
            file_name="audora_result.json",
            mime="application/json",
            use_container_width=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# EMPTY STATE
# ══════════════════════════════════════════════════════════════════════════════

elif not run_button:
    st.markdown(
        '<div class="card" style="text-align:center;padding:3rem;">'
        '<p style="font-size:3rem;margin-bottom:1rem">🎓</p>'
        '<h3 style="font-family:\'Syne\',sans-serif;font-weight:700;color:#e8eaf2;margin-bottom:0.5rem">'
        'Upload your materials to begin</h3>'
        '<p style="color:#7b82a0;max-width:480px;margin:0 auto;">'
        'Audora transforms raw lecture audio into structured, syllabus-aligned study notes. '
        'Upload your lecture recording (MP3/MP4) and optionally your course syllabus (PDF) '
        'to generate AI-powered clean notes with Exam Radar alerts.'
        '</p>'
        '</div>',
        unsafe_allow_html=True,
    )