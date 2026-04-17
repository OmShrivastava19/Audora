import json
import html
import hashlib
import os
import random
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


def _notes_fingerprint(result: dict) -> str:
    payload = json.dumps(result or {}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _extract_any_json(raw: str):
    if not isinstance(raw, str):
        return {}
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


def _compact_notes_for_practice(result: dict, max_chars: int = 9000) -> str:
    parts = []
    summary = str(result.get("summary", "") or "").strip()
    if summary:
        parts.append(f"Summary: {summary[:900]}")

    notes = result.get("notes", [])
    if not isinstance(notes, list):
        notes = []

    for note in notes[:18]:
        if not isinstance(note, dict):
            continue
        module = str(note.get("module", "General") or "General").strip()
        content = str(note.get("content", "") or "").strip()
        if not content:
            continue
        parts.append(f"Module: {module}\nKey content: {content[:700]}")

    compact = "\n\n".join(parts).strip()
    if len(compact) <= max_chars:
        return compact
    return compact[:max_chars]


def build_practice_prompt_from_notes(structured_notes: dict) -> str:
    """Build a compact prompt to generate flashcards and mixed quiz items from structured notes."""
    title = str(structured_notes.get("title", "Lecture Notes") or "Lecture Notes")
    language = str(structured_notes.get("language", "en") or "en")
    modules = []
    for note in structured_notes.get("notes", []):
        if not isinstance(note, dict):
            continue
        module = str(note.get("module", "General") or "General").strip()
        if module and module not in modules:
            modules.append(module)
    compact_notes = _compact_notes_for_practice(structured_notes)

    return f"""
You are a study practice generator.
Create retrieval-practice content from the notes below.

Rules:
- Return JSON only.
- Generate 10 to 30 flashcards.
- Flashcard fields: question, answer, module, difficulty (easy|medium|hard).
- Generate 20 quiz items with mixed types: mcq, short_answer, true_false.
- Each quiz item fields: id, type, module, difficulty, question, explanation.
- For mcq: include options (exactly 4) and correct_index (0-3).
- For short_answer: include answer as concise expected answer.
- For true_false: include answer as boolean true/false.
- Keep wording precise, exam-focused, and grounded in source notes.

Required output schema:
{{
  "metadata": {{
    "title": "{title}",
    "language": "{language}",
    "generated_from_modules": {json.dumps(modules, ensure_ascii=False)}
  }},
  "flashcards": [{{"question": "...", "answer": "...", "module": "...", "difficulty": "easy"}}],
  "quiz": [{{"id": "q1", "type": "mcq", "module": "...", "difficulty": "medium", "question": "...", "options": ["A", "B", "C", "D"], "correct_index": 0, "explanation": "..."}}]
}}

SOURCE NOTES:
{compact_notes}
""".strip()


def generate_practice_with_groq(structured_notes: dict, groq_key: str) -> dict:
    """Generate practice payload with Groq using notes JSON as source of truth."""
    if not GROQ_OK:
        raise RuntimeError("groq package not installed. Run: pip install groq")
    if not groq_key:
        raise ValueError("Groq API key missing.")

    prompt = build_practice_prompt_from_notes(structured_notes)
    client = Groq(api_key=groq_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=3200,
    )
    return _extract_any_json(response.choices[0].message.content.strip())


def generate_practice_with_openai(structured_notes: dict, api_key: str) -> dict:
    """Generate practice payload with OpenAI using notes JSON as source of truth."""
    prompt = build_practice_prompt_from_notes(structured_notes)

    if LANGCHAIN_OK:
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            max_tokens=3200,
            openai_api_key=api_key,
        )
        messages = [
            SystemMessage(content="Return valid JSON only."),
            HumanMessage(content=prompt),
        ]
        response = llm.invoke(messages)
        return _extract_any_json(response.content.strip())

    if not OPENAI_OK:
        raise RuntimeError("Neither langchain-openai nor openai package is available.")

    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.1,
        messages=[
            {"role": "system", "content": "Return valid JSON only."},
            {"role": "user", "content": prompt},
        ],
    )
    return _extract_any_json(response.choices[0].message.content.strip())


def _fallback_practice_from_notes(notes_result: dict) -> dict:
    notes = notes_result.get("notes", [])
    if not isinstance(notes, list):
        notes = []

    modules = []
    flashcards = []
    quiz = []

    for idx, note in enumerate(notes, start=1):
        if not isinstance(note, dict):
            continue
        module = str(note.get("module", "General") or "General").strip() or "General"
        content = str(note.get("content", "") or "").strip()
        if not content:
            continue
        if module not in modules:
            modules.append(module)

        answer = content[:320]
        flashcards.append(
            {
                "question": f"What is the key idea in {module}?",
                "answer": answer,
                "module": module,
                "difficulty": "medium",
            }
        )

        quiz.append(
            {
                "id": f"short_{idx}",
                "type": "short_answer",
                "module": module,
                "difficulty": "medium",
                "question": f"Summarize a core concept from {module}.",
                "answer": answer,
                "explanation": "Derived from generated notes.",
            }
        )
        quiz.append(
            {
                "id": f"tf_{idx}",
                "type": "true_false",
                "module": module,
                "difficulty": "easy",
                "question": f"The notes include at least one examinable idea in {module}.",
                "answer": True,
                "explanation": "This statement reflects the extracted note content.",
            }
        )

    if not flashcards:
        flashcards = [
            {
                "question": "What is the main takeaway from this lecture?",
                "answer": str(notes_result.get("summary", "Review the generated notes.") or "Review the generated notes."),
                "module": "General",
                "difficulty": "easy",
            }
        ]

    for idx, card in enumerate(list(flashcards), start=1):
        if len(quiz) >= 20:
            break
        answer = card.get("answer", "")
        module = card.get("module", "General")
        question = card.get("question", "")
        options = [
            f"{answer[:70]}",
            "Only administrative announcements",
            "No meaningful concepts discussed",
            "No module-level information present",
        ]
        quiz.append(
            {
                "id": f"mcq_{idx}",
                "type": "mcq",
                "module": module,
                "difficulty": "medium",
                "question": f"Which option best matches this prompt: {question}",
                "options": options,
                "correct_index": 0,
                "explanation": "Option A is grounded in the generated note content.",
            }
        )

    return {
        "metadata": {
            "title": str(notes_result.get("title", "Lecture Notes") or "Lecture Notes"),
            "language": str(notes_result.get("language", "en") or "en"),
            "generated_from_modules": modules or ["General"],
        },
        "flashcards": flashcards[:30],
        "quiz": quiz[:24],
    }


def parse_practice_payload(payload_raw, notes_result: dict) -> dict:
    """Validate and normalize practice JSON payload with graceful fallback for malformed items."""
    payload = payload_raw if isinstance(payload_raw, dict) else _extract_any_json(str(payload_raw))
    if not isinstance(payload, dict):
        payload = {}

    fallback = _fallback_practice_from_notes(notes_result)
    valid_difficulties = {"easy", "medium", "hard"}

    flashcards = []
    for item in payload.get("flashcards", []) if isinstance(payload.get("flashcards", []), list) else []:
        if not isinstance(item, dict):
            continue
        question = str(item.get("question", "") or "").strip()
        answer = str(item.get("answer", "") or "").strip()
        module = str(item.get("module", "General") or "General").strip() or "General"
        difficulty = str(item.get("difficulty", "medium") or "medium").strip().lower()
        if difficulty not in valid_difficulties:
            difficulty = "medium"
        if not question or not answer:
            continue
        flashcards.append(
            {
                "question": question,
                "answer": answer,
                "module": module,
                "difficulty": difficulty,
            }
        )
        if len(flashcards) >= 30:
            break

    quiz = []
    quiz_raw = payload.get("quiz", []) if isinstance(payload.get("quiz", []), list) else []
    for idx, item in enumerate(quiz_raw, start=1):
        if not isinstance(item, dict):
            continue
        q_type = str(item.get("type", "") or "").strip().lower()
        q_type = "true_false" if q_type in {"truefalse", "true_false", "tf"} else q_type
        if q_type not in {"mcq", "short_answer", "true_false"}:
            continue

        question = str(item.get("question", "") or "").strip()
        module = str(item.get("module", "General") or "General").strip() or "General"
        explanation = str(item.get("explanation", "Review this module concept.") or "Review this module concept.").strip()
        difficulty = str(item.get("difficulty", "medium") or "medium").strip().lower()
        if difficulty not in valid_difficulties:
            difficulty = "medium"
        if not question:
            continue

        normalized = {
            "id": str(item.get("id", f"q{idx}") or f"q{idx}"),
            "type": q_type,
            "module": module,
            "difficulty": difficulty,
            "question": question,
            "explanation": explanation,
        }

        if q_type == "mcq":
            options = item.get("options", [])
            if not isinstance(options, list):
                continue
            options = [str(opt).strip() for opt in options if str(opt).strip()]
            if len(options) != 4:
                continue
            try:
                correct_index = int(item.get("correct_index", -1))
            except Exception:
                correct_index = -1
            if correct_index not in (0, 1, 2, 3):
                continue
            normalized["options"] = options
            normalized["correct_index"] = correct_index
        elif q_type == "short_answer":
            answer = str(item.get("answer", "") or "").strip()
            if not answer:
                continue
            normalized["answer"] = answer
        else:
            tf_value = item.get("answer", None)
            if isinstance(tf_value, bool):
                normalized["answer"] = tf_value
            elif isinstance(tf_value, str):
                lowered = tf_value.strip().lower()
                if lowered in {"true", "t", "yes", "1"}:
                    normalized["answer"] = True
                elif lowered in {"false", "f", "no", "0"}:
                    normalized["answer"] = False
                else:
                    continue
            else:
                continue

        quiz.append(normalized)
        if len(quiz) >= 24:
            break

    if len(flashcards) < 10:
        for item in fallback["flashcards"]:
            if len(flashcards) >= 10:
                break
            flashcards.append(item)

    if len(quiz) < 10:
        for item in fallback["quiz"]:
            if len(quiz) >= 20:
                break
            quiz.append(item)

    metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata", {}), dict) else {}
    generated_modules = metadata.get("generated_from_modules")
    if not isinstance(generated_modules, list) or not generated_modules:
        generated_modules = fallback["metadata"].get("generated_from_modules", ["General"])

    return {
        "metadata": {
            "title": str(metadata.get("title", notes_result.get("title", "Lecture Notes")) or "Lecture Notes"),
            "language": str(metadata.get("language", notes_result.get("language", "en")) or "en"),
            "generated_from_modules": [str(module) for module in generated_modules][:30],
        },
        "flashcards": flashcards[:30],
        "quiz": quiz[:24],
    }


def generate_practice_content_from_notes(structured_notes: dict, provider: str, api_key: str) -> dict:
    """Generate and parse study practice content from existing notes using the active provider path."""
    if provider == "groq":
        raw_payload = generate_practice_with_groq(structured_notes, api_key)
    elif provider == "openai":
        raw_payload = generate_practice_with_openai(structured_notes, api_key)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    return parse_practice_payload(raw_payload, structured_notes)


def init_practice_state(practice_payload: dict, cache_key: str):
    """Initialize or refresh practice-specific session state keyed by notes fingerprint."""
    flashcards = practice_payload.get("flashcards", [])
    quiz_bank = practice_payload.get("quiz", [])

    if st.session_state.get("practice_cache_key") == cache_key:
        st.session_state.setdefault("practice_flashcard_order", list(range(len(flashcards))))
        st.session_state.setdefault("practice_flashcard_index", 0)
        st.session_state.setdefault("practice_flashcard_revealed", {})
        st.session_state.setdefault("practice_flashcard_marks", {})
        st.session_state.setdefault("quiz_active_ids", [])
        st.session_state.setdefault("quiz_submitted", False)
        st.session_state.setdefault("quiz_last_result", None)
        st.session_state.setdefault("quiz_timer_started_at", None)
        return

    st.session_state["practice_cache_key"] = cache_key
    st.session_state["practice_flashcard_order"] = list(range(len(flashcards)))
    st.session_state["practice_flashcard_index"] = 0
    st.session_state["practice_flashcard_revealed"] = {}
    st.session_state["practice_flashcard_marks"] = {}

    default_length = 10 if len(quiz_bank) >= 10 else min(5, len(quiz_bank))
    st.session_state["quiz_length"] = default_length
    st.session_state["quiz_timer_enabled"] = False
    st.session_state["quiz_timer_minutes"] = 10
    st.session_state["quiz_timer_started_at"] = None
    st.session_state["quiz_submitted"] = False
    st.session_state["quiz_last_result"] = None
    st.session_state["quiz_active_ids"] = list(range(default_length))


def render_flashcards_ui(practice_payload: dict):
    """Render flashcard practice with reveal, navigation, shuffle, and known/review tracking."""
    flashcards = practice_payload.get("flashcards", [])
    if not flashcards:
        st.info("No flashcards available for this lecture yet.")
        return

    order = st.session_state.get("practice_flashcard_order", list(range(len(flashcards))))
    if len(order) != len(flashcards):
        order = list(range(len(flashcards)))
        st.session_state["practice_flashcard_order"] = order

    index = int(st.session_state.get("practice_flashcard_index", 0) or 0)
    index = max(0, min(index, len(order) - 1))
    st.session_state["practice_flashcard_index"] = index

    marks = st.session_state.get("practice_flashcard_marks", {})
    known_count = sum(1 for value in marks.values() if value == "known")
    review_count = sum(1 for value in marks.values() if value == "review")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(flashcards))
    c2.metric("Known", known_count)
    c3.metric("Review", review_count)

    ctl1, ctl2, ctl3 = st.columns([1.3, 1.3, 2])
    with ctl1:
        if st.button("Shuffle", key="practice_shuffle_flashcards", use_container_width=True):
            shuffled = list(range(len(flashcards)))
            random.shuffle(shuffled)
            st.session_state["practice_flashcard_order"] = shuffled
            st.session_state["practice_flashcard_index"] = 0
            st.rerun()
    with ctl2:
        if st.button("Reset Marks", key="practice_reset_flashcards", use_container_width=True):
            st.session_state["practice_flashcard_marks"] = {}
            st.rerun()
    with ctl3:
        st.caption(f"Card {index + 1} of {len(flashcards)}")

    current_id = order[index]
    card = flashcards[current_id]
    revealed_map = st.session_state.get("practice_flashcard_revealed", {})
    is_revealed = bool(revealed_map.get(current_id, False))

    st.markdown(
        f"<div class='card'>"
        f"<span class='rbadge rbadge-mod'>{html.escape(str(card.get('module', 'General')))}</span>"
        f"<span class='rbadge rbadge-med'>{html.escape(str(card.get('difficulty', 'medium')).upper())}</span>"
        f"<p style='margin-top:0.75rem;font-size:1.02rem;font-weight:600;'>{html.escape(str(card.get('question', '')))}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    reveal_label = "Hide Answer" if is_revealed else "Reveal Answer"
    if st.button(reveal_label, key="practice_reveal_toggle", use_container_width=True):
        revealed_map[current_id] = not is_revealed
        st.session_state["practice_flashcard_revealed"] = revealed_map
        st.rerun()

    if is_revealed:
        st.markdown(
            f"<div class='card card-green'><div class='section-label'>Answer</div><p style='margin:0;line-height:1.7'>{html.escape(str(card.get('answer', '')))}</p></div>",
            unsafe_allow_html=True,
        )

    mark_col1, mark_col2 = st.columns(2)
    with mark_col1:
        if st.button("Mark as Known", key="practice_mark_known", use_container_width=True):
            marks[current_id] = "known"
            st.session_state["practice_flashcard_marks"] = marks
            st.rerun()
    with mark_col2:
        if st.button("Mark as Review", key="practice_mark_review", use_container_width=True):
            marks[current_id] = "review"
            st.session_state["practice_flashcard_marks"] = marks
            st.rerun()

    nav1, nav2 = st.columns(2)
    with nav1:
        if st.button("Previous", key="practice_prev_flashcard", use_container_width=True, disabled=index <= 0):
            st.session_state["practice_flashcard_index"] = max(0, index - 1)
            st.rerun()
    with nav2:
        if st.button("Next", key="practice_next_flashcard", use_container_width=True, disabled=index >= len(order) - 1):
            st.session_state["practice_flashcard_index"] = min(len(order) - 1, index + 1)
            st.rerun()


def _normalize_answer_text(value: str) -> str:
    text = str(value or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_short_answer_correct(expected: str, user_answer: str) -> bool:
    expected_norm = _normalize_answer_text(expected)
    user_norm = _normalize_answer_text(user_answer)
    if not expected_norm or not user_norm:
        return False
    if expected_norm in user_norm or user_norm in expected_norm:
        return True
    expected_terms = {term for term in expected_norm.split(" ") if len(term) > 2}
    user_terms = {term for term in user_norm.split(" ") if len(term) > 2}
    if not expected_terms or not user_terms:
        return False
    overlap = len(expected_terms & user_terms)
    return (overlap / max(1, len(expected_terms))) >= 0.5


def _quiz_answer_to_text(question: dict, answer_value) -> str:
    q_type = question.get("type")
    if q_type == "mcq":
        try:
            idx = int(answer_value)
        except Exception:
            return "No answer"
        options = question.get("options", [])
        if isinstance(options, list) and 0 <= idx < len(options):
            return str(options[idx])
        return "No answer"
    if q_type == "true_false":
        return "True" if bool(answer_value) else "False"
    value = str(answer_value or "").strip()
    return value if value else "No answer"


def _quiz_correct_answer_text(question: dict) -> str:
    q_type = question.get("type")
    if q_type == "mcq":
        options = question.get("options", [])
        idx = int(question.get("correct_index", 0) or 0)
        if isinstance(options, list) and 0 <= idx < len(options):
            return str(options[idx])
        return "Unknown"
    if q_type == "true_false":
        return "True" if bool(question.get("answer", False)) else "False"
    return str(question.get("answer", "")).strip() or "Unknown"


def render_quiz_ui(practice_payload: dict):
    """Render mixed quiz with configurable length, timer option, scoring, and retry-wrong flow."""
    quiz_bank = practice_payload.get("quiz", [])
    if not quiz_bank:
        st.info("No quiz questions available for this lecture yet.")
        return

    available_lengths = [option for option in (5, 10, 20) if option <= len(quiz_bank)]
    if not available_lengths:
        available_lengths = [len(quiz_bank)]

    selected_length = st.selectbox(
        "Quiz length",
        options=available_lengths,
        index=available_lengths.index(st.session_state.get("quiz_length", available_lengths[0]))
        if st.session_state.get("quiz_length", available_lengths[0]) in available_lengths
        else 0,
        key="quiz_length_selector",
    )
    st.session_state["quiz_length"] = selected_length

    timer_enabled = st.checkbox("Enable timer", value=bool(st.session_state.get("quiz_timer_enabled", False)), key="quiz_timer_toggle")
    st.session_state["quiz_timer_enabled"] = timer_enabled

    if timer_enabled:
        minutes = st.number_input(
            "Quiz timer (minutes)",
            min_value=1,
            max_value=120,
            value=int(st.session_state.get("quiz_timer_minutes", 10) or 10),
            step=1,
            key="quiz_timer_minutes_input",
        )
        st.session_state["quiz_timer_minutes"] = int(minutes)

    active_ids = st.session_state.get("quiz_active_ids", [])
    if (
        not isinstance(active_ids, list)
        or len(active_ids) != selected_length
        or any((not isinstance(i, int) or i < 0 or i >= len(quiz_bank)) for i in active_ids)
    ):
        active_ids = random.sample(list(range(len(quiz_bank))), k=selected_length)
        st.session_state["quiz_active_ids"] = active_ids
        st.session_state["quiz_submitted"] = False
        st.session_state["quiz_last_result"] = None

    action_col1, action_col2 = st.columns(2)
    with action_col1:
        if st.button("New Quiz Set", key="quiz_new_set", use_container_width=True):
            st.session_state["quiz_active_ids"] = random.sample(list(range(len(quiz_bank))), k=selected_length)
            st.session_state["quiz_submitted"] = False
            st.session_state["quiz_last_result"] = None
            st.session_state["quiz_timer_started_at"] = None
            st.rerun()
    with action_col2:
        if timer_enabled:
            if st.button("Start Timer", key="quiz_start_timer", use_container_width=True):
                st.session_state["quiz_timer_started_at"] = time.time()
                st.rerun()

    if timer_enabled and st.session_state.get("quiz_timer_started_at"):
        elapsed = int(time.time() - st.session_state["quiz_timer_started_at"])
        total_seconds = int(st.session_state.get("quiz_timer_minutes", 10) * 60)
        remaining = max(0, total_seconds - elapsed)
        minutes_left = remaining // 60
        seconds_left = remaining % 60
        st.caption(f"Time remaining: {minutes_left:02d}:{seconds_left:02d}")
        if remaining <= 0 and not st.session_state.get("quiz_submitted", False):
            st.warning("Timer ended. Submit now to score this attempt.")

    for q_no, qid in enumerate(st.session_state.get("quiz_active_ids", []), start=1):
        question = quiz_bank[qid]
        q_type = question.get("type")
        q_key = f"quiz_answer_{qid}"
        module = str(question.get("module", "General") or "General")
        difficulty = str(question.get("difficulty", "medium") or "medium").upper()

        st.markdown(
            f"<div class='card'>"
            f"<div class='section-label'>Question {q_no}</div>"
            f"<span class='rbadge rbadge-mod'>{html.escape(module)}</span>"
            f"<span class='rbadge rbadge-med'>{html.escape(difficulty)}</span>"
            f"<p style='margin-top:0.75rem;font-weight:600'>{html.escape(str(question.get('question', '')))}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

        if q_type == "mcq":
            options = question.get("options", [])
            st.radio(
                f"Select answer for question {q_no}",
                options=list(range(len(options))),
                format_func=lambda i: options[i],
                key=q_key,
                horizontal=False,
                index=None,
            )
        elif q_type == "true_false":
            st.radio(
                f"True/False for question {q_no}",
                options=[True, False],
                format_func=lambda v: "True" if v else "False",
                key=q_key,
                index=None,
                horizontal=True,
            )
        else:
            st.text_input(
                f"Your short answer for question {q_no}",
                key=q_key,
                placeholder="Type your answer...",
            )

    if st.button("Submit Quiz", key="quiz_submit", use_container_width=True):
        score = 0
        wrong_items = []
        module_stats = {}

        for qid in st.session_state.get("quiz_active_ids", []):
            question = quiz_bank[qid]
            q_type = question.get("type")
            q_key = f"quiz_answer_{qid}"
            user_answer = st.session_state.get(q_key)

            is_correct = False
            if q_type == "mcq":
                is_correct = isinstance(user_answer, int) and user_answer == question.get("correct_index")
            elif q_type == "true_false":
                is_correct = user_answer is not None and bool(user_answer) == bool(question.get("answer"))
            else:
                is_correct = _is_short_answer_correct(str(question.get("answer", "")), str(user_answer or ""))

            module = str(question.get("module", "General") or "General")
            stats = module_stats.setdefault(module, {"correct": 0, "total": 0})
            stats["total"] += 1

            if is_correct:
                score += 1
                stats["correct"] += 1
            else:
                wrong_items.append(
                    {
                        "id": qid,
                        "module": module,
                        "question": question.get("question", ""),
                        "your_answer": _quiz_answer_to_text(question, user_answer),
                        "correct_answer": _quiz_correct_answer_text(question),
                        "explanation": question.get("explanation", "Review this concept in notes."),
                    }
                )

        total = len(st.session_state.get("quiz_active_ids", []))
        accuracy = round((score / total) * 100, 2) if total else 0.0
        per_module = []
        for module, stats in module_stats.items():
            module_accuracy = round((stats["correct"] / max(1, stats["total"])) * 100, 2)
            per_module.append(
                {
                    "module": module,
                    "score": f"{stats['correct']}/{stats['total']}",
                    "accuracy_percent": module_accuracy,
                }
            )

        st.session_state["quiz_submitted"] = True
        st.session_state["quiz_last_result"] = {
            "score": score,
            "total": total,
            "accuracy": accuracy,
            "per_module": per_module,
            "wrong_items": wrong_items,
        }
        st.rerun()

    if st.session_state.get("quiz_submitted") and st.session_state.get("quiz_last_result"):
        result = st.session_state["quiz_last_result"]
        m1, m2, m3 = st.columns(3)
        m1.metric("Score", f"{result['score']}/{result['total']}")
        m2.metric("Accuracy", f"{result['accuracy']:.2f}%")
        m3.metric("Wrong", len(result.get("wrong_items", [])))

        st.markdown("#### Per-module performance")
        st.dataframe(result.get("per_module", []), use_container_width=True)

        wrong_items = result.get("wrong_items", [])
        if wrong_items:
            st.markdown("#### Wrong answers with explanations")
            for item in wrong_items:
                st.markdown(
                    f"<div class='card card-red'>"
                    f"<span class='rbadge rbadge-mod'>{html.escape(str(item.get('module', 'General')))}</span>"
                    f"<p style='margin-top:0.6rem;font-weight:600'>{html.escape(str(item.get('question', '')))}</p>"
                    f"<p style='margin:0.4rem 0 0;'><strong>Your answer:</strong> {html.escape(str(item.get('your_answer', 'No answer')))}</p>"
                    f"<p style='margin:0.2rem 0 0;'><strong>Correct answer:</strong> {html.escape(str(item.get('correct_answer', 'Unknown')))}</p>"
                    f"<p style='margin:0.35rem 0 0;color:#7b82a0;'>{html.escape(str(item.get('explanation', 'Review this module concept.')))}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            if st.button("Retry Wrong Questions", key="quiz_retry_wrong", use_container_width=True):
                wrong_ids = [int(item["id"]) for item in wrong_items if str(item.get("id", "")).isdigit()]
                if not wrong_ids:
                    wrong_ids = [item["id"] for item in wrong_items if isinstance(item.get("id"), int)]
                st.session_state["quiz_active_ids"] = wrong_ids[: max(1, min(len(wrong_ids), 20))]
                st.session_state["quiz_submitted"] = False
                st.session_state["quiz_last_result"] = None
                st.session_state["quiz_timer_started_at"] = time.time() if st.session_state.get("quiz_timer_enabled") else None
                st.rerun()
        else:
            st.success("Perfect run. No wrong answers to retry.")


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
    practice_payload = None
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

    progress.progress(86, text="Generating study practice...")
    try:
        practice_payload = generate_practice_content_from_notes(result, provider, api_key)
    except Exception as e:
        st.warning(f"Practice generation failed. Showing notes normally. Details: {e}")
        practice_payload = parse_practice_payload({}, result)

    _, tts_lang = LANGUAGES[selected_language]
    audio_out = b""
    if enable_tts and GTTS_OK:
        progress.progress(92, text="Generating audio notes...")
        audio_out = notes_to_speech(flatten_notes(result), tts_lang)

    progress.progress(100, text="Done")

    st.session_state["audora_result"] = result
    st.session_state["audora_transcript"] = transcript
    st.session_state["audora_audio_out"] = audio_out
    st.session_state["audora_provider"] = provider
    st.session_state["audora_language"] = selected_language

    practice_key = _notes_fingerprint(result)
    st.session_state["practice_payload"] = practice_payload
    st.session_state["practice_payload_key"] = practice_key
    init_practice_state(practice_payload, practice_key)

generated_result = st.session_state.get("audora_result")
if generated_result:
    result = generated_result
    transcript = st.session_state.get("audora_transcript", "")
    audio_out = st.session_state.get("audora_audio_out", b"")
    provider_used = st.session_state.get("audora_provider", provider)
    language_used = st.session_state.get("audora_language", selected_language)

    practice_key = _notes_fingerprint(result)
    practice_payload = st.session_state.get("practice_payload")
    if st.session_state.get("practice_payload_key") != practice_key or not isinstance(practice_payload, dict):
        try:
            practice_payload = generate_practice_content_from_notes(result, provider_used, api_key)
            st.session_state["practice_payload"] = practice_payload
            st.session_state["practice_payload_key"] = practice_key
        except Exception as e:
            st.warning(f"Practice generation failed. Showing notes normally. Details: {e}")
            practice_payload = parse_practice_payload({}, result)
            st.session_state["practice_payload"] = practice_payload
            st.session_state["practice_payload_key"] = practice_key

    init_practice_state(practice_payload, practice_key)

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
    c1.metric("Provider", "Groq" if provider_used == "groq" else "OpenAI")
    c2.metric("Language", language_used)
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
    st.markdown('<div class="section-label">Study Practice</div>', unsafe_allow_html=True)
    practice_tab1, practice_tab2 = st.tabs(["Flashcards", "Quiz"])

    with practice_tab1:
        render_flashcards_ui(practice_payload)
    with practice_tab2:
        render_quiz_ui(practice_payload)

    st.divider()
    dl1, dl2, dl3 = st.columns(3)

    flashcards_json = json.dumps(practice_payload.get("flashcards", []), indent=2, ensure_ascii=False)
    quiz_json = json.dumps(practice_payload.get("quiz", []), indent=2, ensure_ascii=False)

    revision_lines = [f"{idx}. Q: {card.get('question', '')}\nA: {card.get('answer', '')}" for idx, card in enumerate(practice_payload.get("flashcards", []), start=1)]
    revision_text = "\n\n".join(revision_lines)

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

    dl4, dl5, dl6 = st.columns(3)
    with dl4:
        st.download_button(
            "Download Flashcards JSON",
            data=flashcards_json,
            file_name=f"flashcards_{safe_title}.json",
            mime="application/json",
            use_container_width=True,
        )

    with dl5:
        st.download_button(
            "Download Quiz JSON",
            data=quiz_json,
            file_name=f"quiz_{safe_title}.json",
            mime="application/json",
            use_container_width=True,
        )

    with dl6:
        st.download_button(
            "Download Revision Set",
            data=revision_text,
            file_name=f"revision_set_{safe_title}.txt",
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
