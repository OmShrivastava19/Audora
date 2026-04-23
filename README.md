# Audora 🎓

Curriculum-grounded AI for automated lecture synthesis. React frontend + FastAPI backend.

Audora turns lecture audio/video into clean study notes, maps content to your syllabus modules, flags exam hints, and can read notes back as audio.

## ✨ Stack (Unified)

   - **Backend**: FastAPI + Python
   - **Frontend**: React + TypeScript + Tailwind CSS + Vite
   - **Transcription**: Groq Whisper or OpenAI Whisper
   - **LLM**: Groq LLaMA 3.3 70B or OpenAI GPT-4o
- Syllabus retrieval:
   - Groq mode: **Sentence-Transformers + FAISS (local)**
   - OpenAI mode: **OpenAI Embeddings + FAISS (LangChain)**
- PDF extraction: **PyPDF2 + OCR fallback for scanned PDFs**
- OCR stack: **pypdfium2 + pytesseract + Pillow**
- Audio notes (TTS): **gTTS**
   - Authentication: **Firebase** (email/password + Google OAuth)

## 🚀 Quick Start

1. Clone and enter project:

```bash
git clone https://github.com/OmShrivastava19/Audora.git
cd Audora
```

2. Configure environment:

```bash
# Copy and fill in your API keys
cp .env.example .env
# Edit .env with your Firebase, Groq, and OpenAI keys
```

3. Start the backend:

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Or (macOS/Linux)
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Start backend server (runs on http://localhost:8000)
python -m uvicorn backend.main:app --reload
```

4. Start the frontend (in another terminal):

```bash
cd frontend
npm install  # If not already installed
npm run dev   # Runs on http://localhost:8501

# Windows PowerShell (OpenAI paid mode)
$env:OPENAI_API_KEY="sk-..."

# macOS/Linux (Groq free mode)
export GROQ_API_KEY="gsk_..."

# macOS/Linux (OpenAI paid mode)
export OPENAI_API_KEY="sk-..."
```

5. Open the app:

- Frontend: http://localhost:8501
- Backend API: http://localhost:8000

## 🔑 API Key

For Groq mode, use one free key from https://console.groq.com.

For OpenAI mode, use your paid OpenAI API key.

## 📖 Usage

1. (Optional) Upload syllabus (`.pdf` or `.txt`)
2. Upload lecture file (`.mp3`, `.mp4`, `.m4a`, `.wav`, `.ogg`, `.flac`, `.webm`, `.mpeg`, `.mpga`)
3. Choose output language
4. Click **Generate Notes**
5. Review:
   - Clean Study Notes
   - Source-linked note references with transcript timestamps and quote previews
   - Syllabus coverage heatmap (Covered / Partial / Missing) with evidence snippets
   - Confidence score, label, and reason for every note
   - Exam Radar hints
   - Study Practice tabs:
     - Flashcards (reveal, previous/next, shuffle, known/review tracking)
     - Quiz Mode (MCQ + short answer + true/false, configurable length, optional timer, scoring + retry wrong)
   - Raw transcript preview
   - Downloads (`.md`, notes `.json`, transcript `.txt`, flashcards `.json`, quiz `.json`, revision set `.txt`)

### Source-linked Notes

- Audora transcribes lectures into timestamped segments (`segment_id`, `start_sec`, `end_sec`, `text`) and keeps a merged transcript string for downstream steps.
- Note bullets include structured `references` where available.
- If a model response omits references, Audora automatically aligns each bullet to the most similar transcript segment(s) and attaches fallback references.
- In the UI, each note shows clickable timestamp chips and quote previews to verify evidence.
- Clicking a source chip highlights the matched transcript segment and attempts to jump the lecture audio player.

### Syllabus Coverage Heatmap

- After note generation, Audora computes module-wise lecture coverage from syllabus modules/topics using semantic similarity against transcript evidence.
- Each module reports:
   - `coverage_percent` (0 to 100)
   - `status`: Covered, Partial, or Missing
   - `evidence_count`
   - top evidence snippets
- Thresholds:
   - Covered: >= 70%
   - Partial: 25% to 69%
   - Missing: < 25%
- Coverage summary is included in JSON export and rendered in the app as a heatmap-like table.

### OCR for Scanned Syllabus PDFs

Audora first tries embedded text extraction with PyPDF2. If the syllabus PDF looks scanned or yields very little text, it falls back to OCR page-by-page.

To enable OCR support, install the Python packages:

```bash
pip install pypdfium2 pytesseract Pillow
```

On Windows, you also need the Tesseract runtime. A simple install path is:

```powershell
winget install UB-Mannheim.TesseractOCR
```

If OCR dependencies are missing, the app continues gracefully and shows a warning with install guidance.

### Large Lecture Support

- Files `<=25MB`: transcribed in a single request (same behavior as before).
- Files `>25MB`: automatically split into safe chunks, transcribed sequentially with retry/backoff, then merged in order.
- UI shows live progress for chunk prep, per-chunk transcription, and merge.

## 🧱 Architecture

1. Syllabus extraction (`PyPDF2`) → chunking
2. Provider branch from sidebar toggle:
   - Groq mode: local embeddings (`all-MiniLM-L6-v2`) + local FAISS
   - OpenAI mode: OpenAI embeddings + FAISS via LangChain
3. Audio/video transcription:
   - Groq mode: Groq Whisper
   - OpenAI mode: OpenAI Whisper
4. Syllabus-context retrieval and grounding
5. Structured note generation:
   - Groq mode: Groq LLaMA 3.3 70B
   - OpenAI mode: GPT-4o
6. Deterministic confidence enrichment for each generated note
7. Optional gTTS audio output
8. Source-reference attachment and fallback alignment
9. Syllabus coverage scoring with module evidence

## 📦 Dependencies

- `groq`
- `openai`
- `langchain`
- `langchain-openai`
- `langchain-community`
- `langchain-text-splitters`
- `sentence-transformers`
- `faiss-cpu`
- `numpy`
- `PyPDF2`
- `pypdfium2`
- `pytesseract`
- `Pillow`
- `gTTS`
- `pydub`
- `python-dotenv`

## ⚠️ Limits / Notes

- Groq free transcription endpoint has request size limits (commonly 25MB per file in free tier). Audora now handles this by chunking large uploads automatically.
- Large file chunking requires `pydub` and a working `ffmpeg` installation available on your system PATH.
- `sentence-transformers` downloads the embedding model on first run (Groq mode).
- TTS (`gTTS`) requires internet access.
- OCR fallback requires `pypdfium2`, `pytesseract`, and `Pillow`, plus the Tesseract runtime on your machine.
- On Windows, install Tesseract with `winget install UB-Mannheim.TesseractOCR` or add your existing install to `PATH`.
- Audio timestamp seek support depends on browser/player capabilities. If direct seek is unavailable, Audora shows the exact timestamp for manual seeking.

## 🔐 Privacy

- Groq mode: syllabus embedding + retrieval run locally, and AI steps are sent to Groq over HTTPS.
- OpenAI mode: transcription and LLM calls are sent to OpenAI over HTTPS.
- Keys are read from env or entered in the UI session and not persisted by app logic.

## 📄 License

MIT. See [LICENSE](LICENSE).