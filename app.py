import json
import html
import os
import re
import tempfile
import time
import traceback
from io import BytesIO
from pathlib import Path

import streamlit as st

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

# Optional imports
try:
    from groq import Groq
    GROQ_OK = True
    GROQ_ERROR = None
except ImportError as e:
    Groq = None
    GROQ_OK = False
    GROQ_ERROR = str(e)

try:
    import openai

    OPENAI_OK = True
    OPENAI_ERROR = None
except ImportError as e:
    openai = None
    OPENAI_OK = False
    OPENAI_ERROR = str(e)

try:
    from sentence_transformers import SentenceTransformer

    SBERT_OK = True
    SBERT_ERROR = None
except ImportError as e:
    SentenceTransformer = None
    SBERT_OK = False
    SBERT_ERROR = str(e)

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

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS as LCFAISS

    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        from langchain.text_splitter import RecursiveCharacterTextSplitter

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
    except ImportError:
        from langchain.schema import HumanMessage, SystemMessage

    LANGCHAIN_OK = True
    LANGCHAIN_ERROR = None
except ImportError as e:
    ChatOpenAI = None
    OpenAIEmbeddings = None
    LCFAISS = None
    RecursiveCharacterTextSplitter = None
    HumanMessage = None
    SystemMessage = None
    LANGCHAIN_OK = False
    LANGCHAIN_ERROR = str(e)

try:
    import PyPDF2

    PYPDF2_OK = True
    PYPDF2_ERROR = None
except ImportError as e:
    PyPDF2 = None
    PYPDF2_OK = False
    PYPDF2_ERROR = str(e)

try:
    import pypdfium2 as pdfium

    PDFIUM_OK = True
    PDFIUM_ERROR = None
except ImportError as e:
    pdfium = None
    PDFIUM_OK = False
    PDFIUM_ERROR = str(e)

try:
    from PIL import Image

    PIL_OK = True
    PIL_ERROR = None
except ImportError as e:
    Image = None
    PIL_OK = False
    PIL_ERROR = str(e)

try:
    import pytesseract

    PYTESSERACT_OK = True
    PYTESSERACT_ERROR = None
except ImportError as e:
    pytesseract = None
    PYTESSERACT_OK = False
    PYTESSERACT_ERROR = str(e)

if PYTESSERACT_OK:
    try:
        pytesseract.get_tesseract_version()
        TESSERACT_RUNTIME_OK = True
        TESSERACT_RUNTIME_ERROR = None
    except Exception as e:
        TESSERACT_RUNTIME_OK = False
        TESSERACT_RUNTIME_ERROR = str(e)
else:
    TESSERACT_RUNTIME_OK = False
    TESSERACT_RUNTIME_ERROR = "pytesseract is not installed"

try:
    from gtts import gTTS

    GTTS_OK = True
    GTTS_ERROR = None
except ImportError as e:
    gTTS = None
    GTTS_OK = False
    GTTS_ERROR = str(e)

try:
    from pydub import AudioSegment

    PYDUB_OK = True
    PYDUB_ERROR = None
except ImportError as e:
    AudioSegment = None
    PYDUB_OK = False
    PYDUB_ERROR = str(e)


def _ocr_stack_ready() -> bool:
    return PDFIUM_OK and PIL_OK and PYTESSERACT_OK and TESSERACT_RUNTIME_OK


def _ocr_install_message() -> str:
    return (
        f"OCR fallback is unavailable because one or more OCR dependencies are missing. "
        f"Install them with: {OCR_DEPENDENCY_HINT}. "
        f"On Windows, also install the Tesseract runtime, for example: winget install UB-Mannheim.TesseractOCR."
    )


def _text_signal_score(text: str) -> float:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return 0.0
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9+/_-]{1,}", cleaned)
    visible_chars = sum(1 for char in cleaned if not char.isspace())
    alpha_chars = sum(1 for char in cleaned if char.isalpha())
    alpha_ratio = alpha_chars / max(visible_chars, 1)
    unique_ratio = len({word.lower() for word in words}) / max(len(words), 1)
    score = 0.0
    score += min(len(cleaned) / 400.0, 1.0) * 0.35
    score += min(len(words) / 40.0, 1.0) * 0.35
    score += alpha_ratio * 0.2
    score += unique_ratio * 0.1
    return min(score, 1.0)


def maybe_needs_ocr(extracted_text: str) -> bool:
    cleaned = re.sub(r"\s+", " ", extracted_text or "").strip()
    if not cleaned:
        return True
    if _text_signal_score(cleaned) < 0.45:
        return True
    if re.search(r"\b(cid:\d+|xref|obj|endobj)\b", cleaned, re.IGNORECASE):
        return True
    if re.search(r"[\uFFFD\u25A1]{2,}", cleaned):
        return True
    return False


def _extract_pdf_text_layer1(pdf_bytes: bytes) -> str:
    if not PYPDF2_OK:
        return ""
    try:
        reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
        pages = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(page_text.strip())
        return "\n\n".join(pages).strip()
    except Exception as e:
        st.warning(f"PDF extraction issue: {e}")
        return ""


def ocr_pdf_pages_to_text(pdf_bytes: bytes) -> str:
    if not _ocr_stack_ready():
        st.warning(_ocr_install_message())
        if not PYTESSERACT_OK:
            st.caption(f"Missing pytesseract: {PYTESSERACT_ERROR}")
        elif not PDFIUM_OK:
            st.caption(f"Missing pypdfium2: {PDFIUM_ERROR}")
        elif not PIL_OK:
            st.caption(f"Missing Pillow: {PIL_ERROR}")
        elif not TESSERACT_RUNTIME_OK:
            st.caption(f"Tesseract runtime not available: {TESSERACT_RUNTIME_ERROR}")
        return ""

    tmp_path = None
    page_texts: list[str] = []
    failed_pages: list[int] = []
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name

        document = pdfium.PdfDocument(tmp_path)
        for page_number, page in enumerate(document, start=1):
            try:
                bitmap = page.render(scale=2.0)
                image = bitmap.to_pil()
                if image.mode != "RGB":
                    image = image.convert("RGB")
                text = pytesseract.image_to_string(image).strip()
                if text:
                    page_texts.append(text)
            except Exception:
                failed_pages.append(page_number)

        if failed_pages:
            sample_pages = ", ".join(str(page) for page in failed_pages[:5])
            suffix = "..." if len(failed_pages) > 5 else ""
            st.warning(f"OCR skipped {len(failed_pages)} page(s): {sample_pages}{suffix}")

        return "\n\n".join(page_texts).strip()
    except Exception as e:
        st.warning(f"OCR fallback failed: {e}")
        return ""
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def extract_pdf_text_with_ocr(pdf_bytes: bytes) -> str:
    layer1_text = _extract_pdf_text_layer1(pdf_bytes)
    if layer1_text and not maybe_needs_ocr(layer1_text):
        return layer1_text

    ocr_text = ocr_pdf_pages_to_text(pdf_bytes)
    if ocr_text and _text_signal_score(ocr_text) > _text_signal_score(layer1_text):
        st.toast("OCR fallback used for scanned syllabus PDF", icon="🔎")
        return ocr_text

    if layer1_text:
        if maybe_needs_ocr(layer1_text) and not ocr_text:
            st.warning("Syllabus PDF looks scanned, but OCR could not run. Continuing with the best available extracted text.")
        return layer1_text

    if ocr_text:
        st.toast("OCR fallback used for scanned syllabus PDF", icon="🔎")
        return ocr_text

    st.warning("Could not extract any readable text from the syllabus PDF.")
    return ""


def extract_pdf_text(pdf_bytes: bytes) -> str:
    return extract_pdf_text_with_ocr(pdf_bytes)


st.set_page_config(
    page_title="Audora - Automated Lecture Synthesis",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
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

    .audora-wordmark-sidebar {
        font-family: 'Syne', sans-serif;
        font-weight: 800;
        font-size: 1.9rem;
        letter-spacing: -1px;
        background: linear-gradient(135deg, var(--accent) 0%, #00c4ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
    }

  .audora-tagline {
    font-family: 'DM Mono', monospace;
        font-size: 0.8rem;
    color: var(--muted);
        letter-spacing: 0.5px;
        text-transform: none;
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
  .pill-blue  { background: rgba(0,196,255,0.12); border: 1px solid var(--info); color: var(--info); }
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

  .section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 0.7rem;
  }

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
    .confidence-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        margin: 0.2rem 0 0.9rem;
    }
    .confidence-high { border: 1px solid var(--accent); color: var(--accent); background: rgba(79,255,176,0.10); }
    .confidence-med { border: 1px solid var(--accent3); color: var(--accent3); background: rgba(255,209,102,0.10); }
    .confidence-low { border: 1px solid var(--accent2); color: var(--accent2); background: rgba(255,107,107,0.10); }
    .confidence-reason {
        color: var(--muted);
        font-size: 0.8rem;
        line-height: 1.6;
        margin: 0.25rem 0 0;
    }

  .notes-body { font-size: 1rem; line-height: 1.85; }
  .notes-body h2 {
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--accent);
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.35rem;
  }

  .stButton > button {
    background: var(--accent) !important;
    color: #0d0f14 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.65rem 2rem !important;
    width: 100%;
  }

  [data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
  }

  .stTextInput > div > div > input, .stSelectbox > div > div {
    background: var(--bg) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
    border-radius: 8px !important;
  }

  .stProgress > div > div { background: var(--accent) !important; }
</style>
""",
    unsafe_allow_html=True,
)

AUDORA_SYSTEM_PROMPT = """
You are Audora, an elite academic note-taking AI. Transform a raw lecture
transcript into structured, high-signal study notes guided by the course syllabus.

CORE DIRECTIVES
1. NOISE GATE — discard greetings, admin talk, attendance, discipline remarks,
   jokes, tangents, and filler words.
2. SYLLABUS MAPPING — use official module/topic headers from syllabus context.
3. EXAM RADAR — flag assessment cues like mid-term, final, quiz, assignment,
   important, remember this, or likely exam hints.
4. MULTILINGUAL — if target language is provided, output in that language while
   keeping technical terms in English with translations in parentheses.

Return ONLY JSON with keys:
{
  "title": "...",
  "summary": "...",
    "notes": [{"module": "...", "content": "...", "source_refs": []}],
  "exam_radar": [{"hint": "...", "module": "...", "urgency": "HIGH|MEDIUM", "reason": "..."}],
  "filtered_count": 0,
  "language": "en"
}
"""

LANGUAGES = {
    "English": ("en", "en"),
    "Spanish": ("es", "es"),
    "French": ("fr", "fr"),
    "German": ("de", "de"),
    "Arabic": ("ar", "ar"),
    "Urdu": ("ur", "ur"),
    "Hindi": ("hi", "hi"),
    "Portuguese": ("pt", "pt"),
    "Japanese": ("ja", "ja"),
    "Mandarin": ("zh-CN", "zh"),
}

SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".mp4", ".m4a", ".wav", ".ogg", ".flac", ".webm", ".mpeg", ".mpga"}

CONTENT_TYPES = {
    ".mp3": "audio/mpeg",
    ".mp4": "audio/mp4",
    ".m4a": "audio/mp4",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".webm": "audio/webm",
    ".mpeg": "audio/mpeg",
    ".mpga": "audio/mpeg",
}

OCR_DEPENDENCY_HINT = "pip install pypdfium2 pytesseract Pillow"

GENERIC_NOTE_PHRASES = [
    "general overview",
    "key points",
    "important points",
    "this section",
    "summary of lecture",
    "general notes",
    "basic introduction",
    "review the topic",
]

STOPWORDS = {
    "a",
    "about",
    "after",
    "all",
    "also",
    "and",
    "are",
    "as",
    "at",
    "be",
    "because",
    "but",
    "by",
    "can",
    "class",
    "course",
    "for",
    "from",
    "get",
    "has",
    "have",
    "he",
    "her",
    "his",
    "how",
    "if",
    "in",
    "into",
    "is",
    "it",
    "lecture",
    "module",
    "notes",
    "of",
    "on",
    "or",
    "our",
    "out",
    "page",
    "pdf",
    "section",
    "that",
    "the",
    "their",
    "this",
    "to",
    "topic",
    "up",
    "was",
    "we",
    "were",
    "what",
    "when",
    "which",
    "with",
    "you",
    "your",
}


def get_env_key(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        return (st.secrets.get(name, "") or "").strip()
    except Exception:
        return ""


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


@st.cache_resource(show_spinner="Loading local embedding model (first run may take a minute)...")
def load_embedding_model():
    if not SBERT_OK:
        return None
    return SentenceTransformer("all-MiniLM-L6-v2")


class SyllabusVectorStore:
    def __init__(self, chunks: list[str], model):
        self.chunks = chunks
        embeddings = model.encode(
            chunks,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
        ).astype("float32")
        faiss.normalize_L2(embeddings)
        self.index = faiss.IndexFlatIP(embeddings.shape[1])
        self.index.add(embeddings)
        self.model = model

    def search(self, query: str, k: int = 8) -> list[str]:
        k = min(k, len(self.chunks))
        query_vec = self.model.encode([query], show_progress_bar=False, convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(query_vec)
        _, indices = self.index.search(query_vec, k)
        return [self.chunks[i] for i in indices[0] if 0 <= i < len(self.chunks)]


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> list[str]:
    if not text.strip():
        return []
    for sep in ["\n\n", "\n", ". ", " "]:
        if sep not in text:
            continue
        raw = text.split(sep)
        chunks = []
        current = ""
        for part in raw:
            candidate = f"{current}{sep}{part}" if current else part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current.strip():
                    chunks.append(current.strip())
                current = part
        if current.strip():
            chunks.append(current.strip())

        overlapped = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped.append(chunk)
            else:
                tail = chunks[i - 1][-overlap:]
                overlapped.append((tail + " " + chunk).strip())
        return [c for c in overlapped if c.strip()]

    step = max(1, chunk_size - overlap)
    return [text[i : i + chunk_size] for i in range(0, len(text), step)]


def build_groq_vector_store(syllabus_text: str):
    if not (SBERT_OK and FAISS_OK):
        return None
    model = load_embedding_model()
    if model is None:
        return None
    chunks = chunk_text(syllabus_text)
    if not chunks:
        return None
    return SyllabusVectorStore(chunks, model)


def build_openai_vector_store(syllabus_text: str, api_key: str):
    if not LANGCHAIN_OK:
        return None
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_text(syllabus_text)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)
    return LCFAISS.from_texts(chunks, embeddings)


def get_syllabus_context(vector_store, query: str, provider: str) -> str:
    if vector_store is None:
        return ""
    if provider == "groq":
        return "\n---\n".join(vector_store.search(query, k=8))
    docs = vector_store.similarity_search(query, k=8)
    return "\n---\n".join([d.page_content for d in docs])


def _validate_audio_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower() or ".mp3"
    if suffix not in SUPPORTED_AUDIO_EXTENSIONS:
        raise ValueError(
            f"Unsupported audio format '{suffix}'. Supported formats: {', '.join(sorted(SUPPORTED_AUDIO_EXTENSIONS))}"
        )
    return suffix


def _cleanup_temp_paths(paths: list[str]):
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.unlink(path)
        except Exception:
            pass


def _is_non_retryable_transcription_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    hard_fail_markers = [
        "invalid api key",
        "incorrect api key",
        "authentication",
        "unauthorized",
        "permission",
        "unsupported",
        "invalid file format",
        "model_not_found",
    ]
    return any(marker in msg for marker in hard_fail_markers)


def _run_with_retries(fn, max_retries: int = 4, base_delay: float = 1.5, max_delay: float = 12.0):
    for attempt in range(1, max_retries + 1):
        try:
            return fn()
        except Exception as exc:
            if _is_non_retryable_transcription_error(exc) or attempt >= max_retries:
                raise
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            time.sleep(delay)


def chunk_audio(audio_bytes: bytes, filename: str, target_chunk_mb: float = 20.0) -> tuple[list[str], str]:
    """Split large audio into safe temporary chunks and return chunk file paths + suffix."""
    if not audio_bytes:
        raise ValueError("Uploaded lecture file is empty.")
    if not PYDUB_OK:
        raise RuntimeError(
            "Large file chunking requires pydub. Install with: pip install pydub. "
            "Also ensure ffmpeg is installed and available on PATH."
        )

    suffix = _validate_audio_extension(filename)
    target_bytes = int(max(18.0, min(20.0, target_chunk_mb)) * 1024 * 1024)

    input_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as src:
            src.write(audio_bytes)
            input_path = src.name

        audio = AudioSegment.from_file(input_path)
        duration_ms = len(audio)
        if duration_ms <= 0:
            raise ValueError("Could not decode audio stream; duration is zero.")

        bytes_per_ms = max(1.0, len(audio_bytes) / duration_ms)
        chunk_duration_ms = int(target_bytes / bytes_per_ms)
        chunk_duration_ms = max(30_000, chunk_duration_ms)

        chunk_paths: list[str] = []
        start_ms = 0
        chunk_idx = 1
        while start_ms < duration_ms:
            end_ms = min(start_ms + chunk_duration_ms, duration_ms)
            segment = audio[start_ms:end_ms]
            if len(segment) <= 0:
                break
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as dst:
                segment.export(dst.name, format=suffix.lstrip("."))
                chunk_paths.append(dst.name)
            start_ms = end_ms
            chunk_idx += 1

        if not chunk_paths:
            raise ValueError("Chunking produced no output segments.")
        return chunk_paths, suffix
    except Exception:
        raise
    finally:
        if input_path:
            _cleanup_temp_paths([input_path])


def _transcribe_file_with_groq(file_path: str, filename: str, groq_key: str) -> str:
    suffix = _validate_audio_extension(filename)
    if not GROQ_OK:
        raise RuntimeError("groq package not installed. Run: pip install groq")
    if not groq_key:
        raise ValueError("Groq API key missing.")

    client = Groq(api_key=groq_key)
    with open(file_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
    result = client.audio.transcriptions.create(
        model="whisper-large-v3-turbo",
        file=(filename, audio_bytes, CONTENT_TYPES.get(suffix, "audio/mpeg")),
        response_format="text",
    )
    return str(result).strip()


def _transcribe_file_with_openai(file_path: str, api_key: str) -> str:
    if not OPENAI_OK:
        raise RuntimeError("openai package not installed. Run: pip install openai")
    if not api_key:
        raise ValueError("OpenAI API key missing.")

    client = openai.OpenAI(api_key=api_key)
    with open(file_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",
        )
    return str(response).strip()


def transcribe_audio_orchestrator(audio_bytes, filename, provider, api_key, progress_callback=None):
    """Transcribe small files directly and large files via chunking with ordered stitching."""
    suffix = _validate_audio_extension(filename)
    size_mb = len(audio_bytes) / (1024 * 1024)

    if size_mb <= 25:
        if provider == "groq":
            return transcribe_with_groq(audio_bytes, filename, api_key)
        if provider == "openai":
            return transcribe_with_openai(audio_bytes, filename, api_key)
        raise ValueError(f"Unsupported provider: {provider}")

    if progress_callback:
        progress_callback("preparing")

    chunk_paths: list[str] = []
    try:
        chunk_paths, _ = chunk_audio(audio_bytes, filename, target_chunk_mb=20.0)
        total_chunks = len(chunk_paths)

        chunk_transcripts: list[str] = []
        for idx, chunk_path in enumerate(chunk_paths, start=1):
            if progress_callback:
                progress_callback("chunk", idx, total_chunks)

            chunk_filename = f"{Path(filename).stem}_chunk_{idx}{suffix}"
            if provider == "groq":
                text = _run_with_retries(lambda: _transcribe_file_with_groq(chunk_path, chunk_filename, api_key))
            elif provider == "openai":
                text = _run_with_retries(lambda: _transcribe_file_with_openai(chunk_path, api_key))
            else:
                raise ValueError(f"Unsupported provider: {provider}")

            cleaned = text.strip()
            if cleaned:
                chunk_transcripts.append(f"--- Chunk {idx} ---\n{cleaned}")

        if progress_callback:
            progress_callback("merging")

        merged = "\n\n".join(chunk_transcripts).strip()
        if not merged:
            raise RuntimeError("Transcription completed but all chunk outputs were empty.")
        return merged
    finally:
        _cleanup_temp_paths(chunk_paths)


def transcribe_with_groq(audio_bytes: bytes, filename: str, groq_key: str) -> str:
    if not GROQ_OK:
        raise RuntimeError("groq package not installed. Run: pip install groq")
    if not groq_key:
        raise ValueError("Groq API key missing.")
    suffix = _validate_audio_extension(filename)

    client = Groq(api_key=groq_key)
    result = client.audio.transcriptions.create(
        model="whisper-large-v3-turbo",
        file=(filename, audio_bytes, CONTENT_TYPES.get(suffix, "audio/mpeg")),
        response_format="text",
    )
    return str(result).strip()


def transcribe_with_openai(audio_bytes: bytes, filename: str, api_key: str) -> str:
    if not OPENAI_OK:
        raise RuntimeError("openai package not installed. Run: pip install openai")
    if not api_key:
        raise ValueError("OpenAI API key missing.")

    suffix = _validate_audio_extension(filename)
    tmp_path = None

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        return _transcribe_file_with_openai(tmp_path, api_key)
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def _extract_json(raw: str) -> dict:
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
            "notes": [{"module": "General", "content": raw, "source_refs": []}],
            "exam_radar": [],
            "filtered_count": 0,
            "language": "en",
        }


def _normalize_terms(text: str) -> set[str]:
    terms = set()
    for match in re.finditer(r"[A-Za-z0-9][A-Za-z0-9+/_-]{1,}", text or ""):
        term = match.group(0).lower().strip("-_/")
        if len(term) < 3:
            continue
        if term in STOPWORDS:
            continue
        if term.isdigit():
            continue
        terms.add(term)
    return terms


def _confidence_label(score: float) -> str:
    if score >= 0.75:
        return "HIGH"
    if score >= 0.45:
        return "MEDIUM"
    return "LOW"


def _module_alignment_score(module: str, syllabus_context: str) -> float:
    module_text = (module or "").strip().lower()
    syllabus_text = (syllabus_context or "").strip().lower()
    if not module_text:
        return 0.15 if syllabus_text else 0.2
    if not syllabus_text:
        return 0.35
    if module_text in syllabus_text:
        return 1.0

    module_terms = _normalize_terms(module_text)
    syllabus_terms = _normalize_terms(syllabus_text)
    if not module_terms or not syllabus_terms:
        return 0.3

    overlap = len(module_terms & syllabus_terms)
    ratio = overlap / max(len(module_terms), 1)
    return min(1.0, 0.25 + ratio * 0.75)


def _transcript_overlap_score(content: str, transcript_terms: set[str]) -> float:
    content_terms = _normalize_terms(content)
    if not content_terms or not transcript_terms:
        return 0.0
    overlap = len(content_terms & transcript_terms)
    return min(1.0, overlap / max(len(content_terms), 1))


def _specificity_score(content: str) -> float:
    text = (content or "").strip()
    if not text:
        return 0.0
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9+/_-]{1,}", text)
    word_count = len(words)
    score = 0.0
    if word_count >= 45:
        score = 1.0
    elif word_count >= 30:
        score = 0.85
    elif word_count >= 18:
        score = 0.7
    elif word_count >= 10:
        score = 0.5
    elif word_count >= 5:
        score = 0.25
    else:
        score = 0.1

    if any(symbol in text for symbol in (":", "(", ")", "-", "•")):
        score += 0.05
    if re.search(r"\b\d+\b", text):
        score += 0.05
    return min(score, 1.0)


def _generic_penalty(module: str, content: str, result: dict) -> float:
    combined = f"{module or ''} {content or ''}".strip().lower()
    penalty = 0.0
    if not (content or "").strip():
        penalty += 0.45
    if (module or "").strip().lower() in {"general", "misc", "miscellaneous", "other", "overview"}:
        penalty += 0.12
    if len(_normalize_terms(content)) < 8:
        penalty += 0.08
    for phrase in GENERIC_NOTE_PHRASES:
        if phrase in combined:
            penalty += 0.05
    if any(marker in combined for marker in ("{", "}", '"notes"', '"title"', '"summary"')):
        penalty += 0.15
    if len(result.get("notes", [])) == 1 and not (result.get("summary") or "").strip():
        penalty += 0.05
    return min(penalty, 0.4)


def _build_confidence_reason(module_score: float, transcript_score: float, specificity_score: float, penalty: float, label: str) -> str:
    parts = []
    if module_score >= 0.75:
        parts.append("strong syllabus alignment")
    elif module_score >= 0.45:
        parts.append("partial syllabus alignment")
    else:
        parts.append("weak syllabus alignment")

    if transcript_score >= 0.5:
        parts.append("good transcript overlap")
    elif transcript_score >= 0.25:
        parts.append("moderate transcript overlap")
    else:
        parts.append("limited transcript overlap")

    if specificity_score >= 0.75:
        parts.append("specific content")
    elif specificity_score >= 0.4:
        parts.append("moderately specific content")
    else:
        parts.append("short or generic content")

    if penalty >= 0.15:
        parts.append("generic/fallback penalty applied")

    parts.append(f"label {label}")
    return "; ".join(parts)


def enrich_notes_with_confidence(result, transcript, syllabus_context) -> dict:
    enriched = dict(result or {})
    notes = enriched.get("notes", [])
    if not isinstance(notes, list):
        notes = []

    transcript_terms = _normalize_terms(transcript or "")
    syllabus_text = syllabus_context or ""

    normalized_notes = []
    for note in notes:
        if not isinstance(note, dict):
            note = {"module": "General", "content": str(note)}

        module = str(note.get("module", "General") or "General")
        content = str(note.get("content", "") or "")
        source_refs = note.get("source_refs", [])
        if not isinstance(source_refs, list):
            source_refs = []

        module_score = _module_alignment_score(module, syllabus_text)
        transcript_score = _transcript_overlap_score(content, transcript_terms)
        specificity_score = _specificity_score(content)
        penalty = _generic_penalty(module, content, enriched)

        raw_score = (module_score * 0.4) + (transcript_score * 0.35) + (specificity_score * 0.25) - penalty
        score = max(0.0, min(1.0, round(raw_score, 2)))
        label = _confidence_label(score)
        reason = _build_confidence_reason(module_score, transcript_score, specificity_score, penalty, label)

        normalized_note = dict(note)
        normalized_note["module"] = module
        normalized_note["content"] = content
        normalized_note["source_refs"] = source_refs
        normalized_note["confidence_score"] = score
        normalized_note["confidence_label"] = label
        normalized_note["confidence_reason"] = reason
        normalized_notes.append(normalized_note)

    enriched["notes"] = normalized_notes
    return enriched


def generate_notes_with_groq(transcript: str, syllabus_context: str, groq_key: str, target_language: str) -> dict:
    if not GROQ_OK:
        raise RuntimeError("groq package not installed. Run: pip install groq")

    language_line = (
        f"Write ALL notes and summary in {target_language}. Keep technical terms in English with translations in parentheses."
        if target_language.lower() != "english"
        else ""
    )

    prompt = f"""{AUDORA_SYSTEM_PROMPT}

SYLLABUS CONTEXT
{syllabus_context if syllabus_context else "[No syllabus uploaded]"}

RAW TRANSCRIPT
{transcript}

FINAL INSTRUCTION
{language_line}
Apply all directives and return only the JSON object.
"""

    client = Groq(api_key=groq_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=4096,
    )
    return _extract_json(response.choices[0].message.content.strip())


def generate_notes_with_openai(transcript: str, syllabus_context: str, api_key: str, target_language: str) -> dict:
    language_line = (
        f"Write ALL notes and summary in {target_language}. Keep technical terms in English with translations in parentheses."
        if target_language.lower() != "english"
        else ""
    )

    human = f"""
SYLLABUS CONTEXT
{syllabus_context if syllabus_context else "[No syllabus uploaded]"}

RAW TRANSCRIPT
{transcript}

FINAL INSTRUCTION
{language_line}
Apply all directives and return only the JSON object.
""".strip()

    if LANGCHAIN_OK:
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.2,
            max_tokens=4096,
            openai_api_key=api_key,
        )
        messages = [SystemMessage(content=AUDORA_SYSTEM_PROMPT), HumanMessage(content=human)]
        response = llm.invoke(messages)
        return _extract_json(response.content.strip())

    if not OPENAI_OK:
        raise RuntimeError("Neither langchain-openai nor openai package is available.")

    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        messages=[
            {"role": "system", "content": AUDORA_SYSTEM_PROMPT},
            {"role": "user", "content": human},
        ],
    )
    return _extract_json(response.choices[0].message.content.strip())


def notes_to_speech(notes_text: str, lang_code: str = "en") -> bytes:
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
    summary = result.get("summary", "")
    if summary:
        parts.append(f"Summary. {summary}")
    for note in result.get("notes", []):
        parts.append(f"{note.get('module', '')}. {note.get('content', '')}")
    return "\n\n".join(parts)


with st.sidebar:
    st.markdown('<div class="audora-wordmark-sidebar">AUDORA</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="audora-tagline">Curriculum Grounded AI for Automated Lecture Synthesis</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown("### Model Provider")
    provider_label = st.radio(
        "Select provider",
        options=["Groq (Free)", "OpenAI (Paid)"],
        index=0,
        help="Use Groq for a free flow or OpenAI for paid GPT-4o + Whisper flow.",
    )
    provider = "groq" if provider_label.startswith("Groq") else "openai"

    if provider == "groq":
        key_input = st.text_input(
            "Groq API Key",
            type="password",
            placeholder="gsk_...",
            key="groq_key",
            help="Free key from console.groq.com",
        )
        api_key = key_input or get_env_key("GROQ_API_KEY")
    else:
        key_input = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            key="openai_key",
            help="Paid key from OpenAI dashboard",
        )
        api_key = key_input or get_env_key("OPENAI_API_KEY")

    st.divider()
    st.markdown("### Output Language")
    selected_language = st.selectbox("Target language", options=list(LANGUAGES.keys()), index=0, label_visibility="collapsed")

    st.divider()
    st.markdown("### Accessibility")
    enable_tts = st.checkbox("Generate audio notes (gTTS)", value=True)

    st.divider()
    st.markdown("### Dependency Status")

    checks = [
        ("PyPDF2", PYPDF2_OK, PYPDF2_ERROR),
        (
            "OCR stack (pypdfium2 + pytesseract + Pillow)",
            PDFIUM_OK and PIL_OK and PYTESSERACT_OK and TESSERACT_RUNTIME_OK,
            PDFIUM_ERROR or PIL_ERROR or PYTESSERACT_ERROR or TESSERACT_RUNTIME_ERROR,
        ),
        ("gTTS", GTTS_OK, GTTS_ERROR),
        ("pydub (large file chunking)", PYDUB_OK, PYDUB_ERROR),
    ]

    if provider == "groq":
        checks.extend(
            [
                ("groq", GROQ_OK, GROQ_ERROR),
                ("sentence-transformers", SBERT_OK, SBERT_ERROR),
                ("faiss-cpu / numpy", FAISS_OK, FAISS_ERROR),
            ]
        )
    else:
        checks.extend(
            [
                ("openai", OPENAI_OK, OPENAI_ERROR),
                ("langchain-openai", LANGCHAIN_OK, LANGCHAIN_ERROR),
            ]
        )

    for label, ok, err in checks:
        icon = "✅" if ok else "❌"
        st.markdown(f"{icon} {label}")
        if not ok and err:
            st.caption(err)


st.markdown(
    '<h1 class="audora-wordmark" role="heading" aria-level="1">AUDORA</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="audora-tagline">Curriculum Grounded AI for Automated Lecture Synthesis</p>',
    unsafe_allow_html=True,
)
st.divider()

if provider == "groq":
    required_ok = GROQ_OK and SBERT_OK and FAISS_OK
    if not required_ok:
        st.error(
            "Missing packages for Groq mode. Install and restart:\n\n"
            "```bash\n"
            "pip install groq sentence-transformers faiss-cpu numpy PyPDF2 gTTS streamlit python-dotenv\n"
            "```"
        )
else:
    required_ok = OPENAI_OK and LANGCHAIN_OK
    if not required_ok:
        st.error(
            "Missing packages for OpenAI mode. Install and restart:\n\n"
            "```bash\n"
            "pip install openai langchain langchain-openai langchain-community langchain-text-splitters faiss-cpu PyPDF2 gTTS streamlit python-dotenv\n"
            "```"
        )

left_col, right_col = st.columns(2, gap="large")

with left_col:
    st.markdown('<div class="section-label">Course Syllabus (Optional)</div>', unsafe_allow_html=True)
    syllabus_file = st.file_uploader(
        "Upload syllabus (PDF or TXT)",
        type=["pdf", "txt"],
        key="syllabus",
    )

with right_col:
    st.markdown('<div class="section-label">Lecture Recording</div>', unsafe_allow_html=True)
    audio_file = st.file_uploader(
        "Upload lecture (audio/video)",
        type=["mp3", "mp4", "m4a", "wav", "ogg", "flac", "webm", "mpeg", "mpga"],
        key="audio",
    )
    if audio_file:
        size_mb = len(audio_file.getvalue()) / (1024 * 1024)
        st.caption(f"{audio_file.name} - {size_mb:.1f} MB")

st.divider()

_, btn_col, _ = st.columns([2, 3, 2])
with btn_col:
    can_run = bool(api_key) and bool(audio_file) and required_ok
    run_button = st.button(
        "Generate Notes",
        disabled=not can_run,
        use_container_width=True,
    )

if not api_key:
    if provider == "groq":
        st.info("Add your Groq key in the sidebar to continue.")
    else:
        st.info("Add your OpenAI key in the sidebar to continue.")
elif not audio_file:
    st.info("Upload a lecture recording to continue.")

if run_button and can_run:
    result = {}
    transcript = ""
    progress = st.progress(0, text="Starting pipeline...")

    vector_store = None
    if syllabus_file:
        progress.progress(10, text="Processing syllabus...")
        try:
            raw = syllabus_file.read()
            syllabus_text = (
                extract_pdf_text_with_ocr(raw)
                if syllabus_file.name.lower().endswith(".pdf")
                else raw.decode("utf-8", errors="replace")
            )

            if syllabus_text.strip():
                if provider == "groq":
                    vector_store = build_groq_vector_store(syllabus_text)
                else:
                    vector_store = build_openai_vector_store(syllabus_text, api_key)
                if vector_store is not None:
                    st.toast("Syllabus indexed successfully", icon="📚")
            else:
                st.warning("Could not extract readable syllabus text. Continuing without syllabus context.")
        except Exception as e:
            st.warning(f"Syllabus processing issue: {e}")

    progress.progress(35, text="Transcribing lecture...")
    try:
        audio_bytes = audio_file.getvalue()

        def on_transcription_progress(stage: str, current: int = 0, total: int = 0):
            if stage == "preparing":
                progress.progress(36, text="Preparing chunks...")
            elif stage == "chunk" and total > 0:
                base = 36
                span = 20
                pct = base + int((current / total) * span)
                progress.progress(min(58, pct), text=f"Transcribing chunk {current} of {total}")
            elif stage == "merging":
                progress.progress(59, text="Merging transcripts...")

        transcript = transcribe_audio_orchestrator(
            audio_bytes=audio_bytes,
            filename=audio_file.name,
            provider=provider,
            api_key=api_key,
            progress_callback=on_transcription_progress,
        )

        if not transcript:
            st.error("Transcription returned empty output.")
            st.stop()
    except Exception as e:
        st.error(f"Transcription failed: {e}")
        with st.expander("Debug details"):
            st.code(traceback.format_exc())
        st.stop()

    progress.progress(60, text="Retrieving syllabus context...")
    syllabus_context = get_syllabus_context(vector_store, transcript[:4000], provider)

    progress.progress(78, text="Generating structured notes...")
    try:
        if provider == "groq":
            result = generate_notes_with_groq(transcript, syllabus_context, api_key, selected_language)
        else:
            result = generate_notes_with_openai(transcript, syllabus_context, api_key, selected_language)
        result = enrich_notes_with_confidence(result, transcript, syllabus_context)
    except Exception as e:
        st.error(f"Note generation failed: {e}")
        with st.expander("Debug details"):
            st.code(traceback.format_exc())
        st.stop()

    _, tts_lang = LANGUAGES[selected_language]
    audio_out = b""
    if enable_tts and GTTS_OK:
        progress.progress(92, text="Generating audio notes...")
        audio_out = notes_to_speech(flatten_notes(result), tts_lang)

    progress.progress(100, text="Done")

    st.divider()

    title = result.get("title", "Lecture Notes")
    summary = result.get("summary", "")
    notes = result.get("notes", [])
    exam_hints = result.get("exam_radar", [])
    filtered_count = result.get("filtered_count", 0)

    st.markdown(
        f"<h2 style='font-family:Syne,sans-serif;font-size:1.75rem;font-weight:800;color:#e8eaf2;'>{title}</h2>",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Provider", "Groq" if provider == "groq" else "OpenAI")
    c2.metric("Language", selected_language)
    c3.metric("Noise Removed", filtered_count)
    c4.metric("Exam Hints", len(exam_hints))

    if summary:
        st.markdown(
            f"<div class='card card-green'><div class='section-label'>Executive Summary</div><p style='margin:0;line-height:1.7'>{summary}</p></div>",
            unsafe_allow_html=True,
        )

    st.divider()

    notes_col, radar_col = st.columns([3, 2], gap="large")

    with notes_col:
        st.markdown('<div class="section-label">Clean Study Notes</div>', unsafe_allow_html=True)
        if notes:
            for note in notes:
                module = note.get("module", "General")
                content = note.get("content", "")
                confidence_label = str(note.get("confidence_label", "LOW")).upper()
                confidence_score = float(note.get("confidence_score", 0.0) or 0.0)
                confidence_reason = note.get("confidence_reason", "")
                source_refs = note.get("source_refs", [])
                confidence_class = "confidence-high" if confidence_label == "HIGH" else "confidence-med" if confidence_label == "MEDIUM" else "confidence-low"
                source_ref_text = ", ".join(str(ref) for ref in source_refs) if source_refs else ""
                source_refs_html = (
                    f"<p class='confidence-reason'>Source refs: {html.escape(source_ref_text)}</p>" if source_ref_text else ""
                )
                card_html = (
                    f"<div class='card'>"
                    f"<div class='section-label'>{html.escape(str(module))}</div>"
                    f"<div class='confidence-row'>"
                    f"<span class='rbadge {confidence_class}'>Confidence {html.escape(confidence_label)}</span>"
                    f"<span class='rbadge rbadge-mod'>{confidence_score:.2f}</span>"
                    f"</div>"
                    f"<div class='notes-body'>{content}</div>"
                    f"<p class='confidence-reason'>{html.escape(confidence_reason)}</p>"
                    f"{source_refs_html}"
                    f"</div>"
                )
                st.markdown(
                    card_html,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No structured notes were returned.")

        if audio_out:
            st.divider()
            st.markdown('<div class="section-label">Audio Notes</div>', unsafe_allow_html=True)
            st.audio(audio_out, format="audio/mp3")

    with radar_col:
        st.markdown('<div class="section-label">Exam Radar</div>', unsafe_allow_html=True)
        if exam_hints:
            for hint in exam_hints:
                urgency = hint.get("urgency", "MEDIUM").upper()
                badge_class = "rbadge-high" if urgency == "HIGH" else "rbadge-med"
                module = hint.get("module", "")
                hint_text = hint.get("hint", "")
                reason = hint.get("reason", "")
                st.markdown(
                    f"<div class='card card-red'>"
                    f"<span class='rbadge {badge_class}'>{urgency}</span>"
                    f"<span class='rbadge rbadge-mod'>{module}</span>"
                    f"<p style='margin:0.55rem 0 0.25rem;font-weight:500;font-size:0.95rem;'>{hint_text}</p>"
                    f"<p style='font-size:0.78rem;color:#7b82a0;margin:0;'>{reason}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                "<div class='card' style='text-align:center;color:#7b82a0;padding:2rem;'>"
                "<p style='font-size:1.8rem;margin-bottom:0.5rem;'>✅</p>"
                "<p style='margin:0;font-size:0.9rem;'>No exam hints detected.</p>"
                "</div>",
                unsafe_allow_html=True,
            )

        st.divider()
        with st.expander("Raw Transcript", expanded=False):
            preview = transcript[:3000] + ("..." if len(transcript) > 3000 else "")
            st.markdown(
                f"<div style='font-family:DM Mono,monospace;font-size:0.78rem;color:#7b82a0;line-height:1.7;white-space:pre-wrap;'>{preview}</div>",
                unsafe_allow_html=True,
            )

    st.divider()
    dl1, dl2, dl3, _ = st.columns([2, 2, 2, 1])

    md_notes = f"# {title}\n\n**Summary:** {summary}\n\n"
    for n in notes:
        confidence_label = str(n.get('confidence_label', 'LOW')).upper()
        confidence_score = float(n.get('confidence_score', 0.0) or 0.0)
        md_notes += (
            f"## {n.get('module', '')}\n\n"
            f"**Confidence:** {confidence_label} ({confidence_score:.2f})\n\n"
            f"**Reason:** {n.get('confidence_reason', '')}\n\n"
            f"{n.get('content', '')}\n\n"
        )
        source_refs = n.get('source_refs', [])
        if source_refs:
            md_notes += f"**Source refs:** {', '.join(str(ref) for ref in source_refs)}\n\n"

    if exam_hints:
        md_notes += "## Exam Radar\n\n"
        for h in exam_hints:
            md_notes += f"- **[{h.get('urgency')}]** {h.get('hint')} *(Module: {h.get('module')})*\n"

    safe_title = re.sub(r"[^a-zA-Z0-9_]", "_", title[:28])

    with dl1:
        st.download_button(
            "Download Notes (Markdown)",
            data=md_notes,
            file_name=f"audora_{safe_title}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with dl2:
        st.download_button(
            "Download Raw JSON",
            data=json.dumps(result, indent=2, ensure_ascii=False),
            file_name="audora_result.json",
            mime="application/json",
            use_container_width=True,
        )

    with dl3:
        st.download_button(
            "Download Transcript",
            data=transcript,
            file_name=f"transcript_{safe_title}.txt",
            mime="text/plain",
            use_container_width=True,
        )

elif not run_button:
    st.markdown(
        "<div class='card' style='text-align:center;padding:2.5rem 2rem;'>"
        "<p style='font-size:2.8rem;margin-bottom:0.8rem;'>🎓</p>"
        "<h3 style='font-family:Syne,sans-serif;font-weight:800;color:#e8eaf2;margin-bottom:0.6rem;'>"
        "Automated Lecture Synthesis"
        "</h3>"
        "<p style='color:#7b82a0;max-width:560px;margin:0 auto;line-height:1.75;font-size:0.92rem;'>"
        "Choose Groq (free) or OpenAI (paid) from the sidebar, add your key, upload lecture audio/video, and generate syllabus-aware notes with exam hints."
        "</p>"
        "</div>",
        unsafe_allow_html=True,
    )
