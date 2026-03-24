# Audora 🎓

Syllabus-aware lecture intelligence for students on a budget.

Audora turns lecture audio/video into clean study notes, maps content to your syllabus modules, flags exam hints, and can read notes back as audio.

## ✨ Stack (Free-First)

- Transcription: **Groq Whisper API** (`whisper-large-v3-turbo`)
- Note generation: **Groq LLaMA 3.3 70B** (`llama-3.3-70b-versatile`)
- Syllabus retrieval: **Sentence-Transformers + FAISS (local)**
- PDF extraction: **PyPDF2**
- Audio notes (TTS): **gTTS**
- UI: **Streamlit**

## 🚀 Quick Start

1. Clone and enter project:

```bash
git clone https://github.com/OmShrivastava19/Audora.git
cd Audora
```

2. Create + activate virtualenv:

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set Groq key (or paste in sidebar):

```bash
# Windows PowerShell
$env:GROQ_API_KEY="gsk_..."

# macOS/Linux
export GROQ_API_KEY="gsk_..."
```

5. Run:

```bash
streamlit run app.py
```

## 🔑 API Key

Audora is designed around **one free key** from https://console.groq.com

- Used for both transcription and note generation
- No OpenAI key required for the free flow in `audora.py`

## 📖 Usage

1. (Optional) Upload syllabus (`.pdf` or `.txt`)
2. Upload lecture file (`.mp3`, `.mp4`, `.m4a`, `.wav`, `.ogg`, `.flac`, `.webm`, `.mpeg`, `.mpga`)
3. Choose output language
4. Click **Generate Notes**
5. Review:
   - Clean Study Notes
   - Exam Radar hints
   - Raw transcript preview
   - Downloads (`.md`, `.json`, transcript `.txt`)

## 🧱 Architecture

1. Syllabus extraction (`PyPDF2`) → chunking
2. Local embeddings (`all-MiniLM-L6-v2`) → FAISS index
3. Audio/video transcription via Groq Whisper
4. Syllabus-context retrieval from local FAISS
5. Structured note generation via Groq LLaMA
6. Optional gTTS audio output

## 📦 Dependencies

- `groq`
- `sentence-transformers`
- `faiss-cpu`
- `numpy`
- `PyPDF2`
- `gTTS`
- `streamlit`
- `python-dotenv`

## ⚠️ Limits / Notes

- Groq free transcription endpoint has request size limits (commonly 25MB per file in free tier).
- `sentence-transformers` downloads the embedding model on first run.
- TTS (`gTTS`) requires internet access.

## 🔐 Privacy

- Syllabus embedding + retrieval run locally.
- Audio/video and transcript processing for AI steps is sent to Groq over HTTPS.
- Keys are read from env/Streamlit input and not persisted by app logic.

## 📄 License

MIT. See [LICENSE](LICENSE).