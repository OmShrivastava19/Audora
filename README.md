# Audora 🎓

**Syllabus-Aware AI Lecture Intelligence System**

Transform raw lecture recordings into structured, high-signal study notes with automatic exam alert detection—powered by OpenAI Whisper, LangChain RAG, and GPT-4o.

---

## ✨ Features

### 📊 Core Intelligence
- **Whisper Transcription**: Converts lecture MP3/MP4 to text with high accuracy (supports mixed-language audio)
- **Syllabus-Grounded RAG**: Vectorizes your course syllabus and uses it as ground truth to structure notes under official module names
- **GPT-4o Analysis**: Intelligently extracts key concepts while filtering noise
- **Automatic Formatting**: Returns clean, structured markdown with proper sections and emphasis

### 🎯 Exam Radar
Detects urgency signals in lectures and flags them with confidence levels:
- Automatically identifies keywords: *final exam, mid-term, quiz, assignment, important, remember, key concept, etc.*
- Returns verbatim professor hints with module mapping and urgency level
- Helps prioritize study focus on high-stakes content

### 🔊 Accessibility & Multilingual
- **Text-to-Speech (TTS)**: Generate MP3 audio versions of notes using gTTS
- **Multilingual Output**: Output notes in 10+ languages while preserving technical terminology in English
- **Screen Reader Friendly**: ARIA labels and semantic HTML throughout
- **Dark Theme**: High-contrast, accessible design optimized for readability

### 🛠️ Noise Gate (Content Filtering)
Automatically removes and doesn't transcribe:
- Greetings, farewells, small-talk
- Administrative announcements (room changes, deadlines)
- Attendance/roll-call
- Off-topic jokes, tangents, or personal anecdotes
- Filler words and repetition

### 📥 Export Options
- **Markdown Download**: Fully formatted notes ready for study apps or wikis
- **JSON Export**: Raw structured data for integration with note-taking systems
- **Audio Download**: MP3 files for offline listening and accessibility

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AUDORA PIPELINE                      │
└─────────────────────────────────────────────────────────┘

1. INGEST
   • Syllabus (PDF/TXT)  ──→  PyPDF2  ──→  Text extraction
   • Lecture (MP3/MP4)   ──→  Whisper ──→  Transcription
                                             (raw, timestamped)

2. VECTORIZATION
   • Syllabus text splits  ──→  RecursiveCharacterTextSplitter
   • Per-chunk embeddings  ──→  OpenAI text-embedding-3-small
   • FAISS index          ──→  In-memory approximate-nearest-neighbor

3. NOISE GATE (Semantic Filter)
   • Raw transcript  ──→  Filter prompt  ──→  Academic segments only

4. SYLLABUS-AWARE RAG
   • Each transcript chunk  ──→  Vectorized query
   • Top-k retrieval        ──→  Syllabus context (ground truth)
   • Injected into LLM      ──→  Official module names guaranteed

5. LLM REASONING (GPT-4o)
   • System prompt    ──→  Noise gate directives + mapping rules
   • Human message    ──→  Syllabus context + transcript
   • Output format    ──→  Structured JSON + exam alerts

6. RENDERING
   • Streamlit UI    ──→  Clean markdown display
   • TTS synthesis   ──→  MP3 audio notes
   • Export options  ──→  MD / JSON downloads
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- OpenAI API key (for Whisper, embeddings, and GPT-4o)
- 256+ MB RAM (FAISS index is in-memory)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/OmShrivastava19/Audora.git
   cd Audora
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   
   # Windows:
   .venv\Scripts\Activate.ps1
   
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your OpenAI API key:**
   ```bash
   # Option A: Environment variable
   export OPENAI_API_KEY="sk-..."
   
   # Option B: Streamlit secrets (~/.streamlit/secrets.toml)
   OPENAI_API_KEY = "sk-..."
   
   # Option C: UI input (sidebar in the app)
   ```

5. **Run the app:**
   ```bash
   streamlit run app.py
   ```

6. **Open in your browser:**
   ```
   http://localhost:8501
   ```

---

## 📖 Usage Guide

### Step 1: Upload Materials (Optional: Syllabus)
- **Syllabus** (PDF or TXT): Recommended for best results. This grounds the note structure in your course's official modules.
- If no syllabus is provided, Audora will use content-based headers.

### Step 2: Upload Lecture Recording
- **Lecture** (MP3, MP4, M4A, or WAV): Can be mono or stereo, mixed languages supported.
- Typical processing: ~10 minutes of audio takes ~2–3 minutes.

### Step 3: Configure (Optional)
- **Output Language**: Select from 10+ languages (defaults to English).
- **Audio Notes**: Enable TTS to generate an MP3 of your notes (great for accessibility and review).

### Step 4: Generate Notes
- Click **"⚡ Generate Notes"** to start the pipeline.
- Watch the progress indicator as Audora:
  1. Vectorizes your syllabus
  2. Transcribes the lecture
  3. Analyzes and structures the notes
  4. Generates audio (if enabled)

### Step 5: Review & Export
- **Clean Notes**: Structured by module, ready for studying.
- **Exam Radar**: Alerts with confidence levels and module mapping.
- **Raw Transcript**: Inspect the full transcription if needed.
- **Download**: Export as Markdown (for Notion, Obsidian, etc.) or raw JSON.

---

## 🔧 Configuration

### Sidebar Options

| Option | Default | Description |
|--------|---------|-------------|
| **OpenAI API Key** | (from env) | Required for Whisper, embeddings, and GPT-4o calls |
| **Output Language** | English | Notes will be written in this language (technical terms remain English) |
| **Audio Notes** | ✅ Enabled | Generate an MP3 audio version of the notes via TTS |

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
PYTHONDONTWRITEBYTECODE=1        # Prevent __pycache__ generation
STREAMLIT_LOGGER_LEVEL=warning   # Reduce log verbosity
```

---

## 📊 Exam Radar Details

The **Exam Radar** feature automatically scans your lecture transcript for exam-relevant signals:

### Trigger Keywords
Audora flags phrases containing:
- **High Urgency**: "final exam", "midterm", "will be tested", "exam question"
- **Medium Urgency**: "important", "remember", "key concept", "assignment", "quiz"

### Output Format
Each flagged hint includes:
```json
{
  "hint": "The heat equation derivation will definitely be on the final.",
  "module": "Partial Differential Equations",
  "urgency": "HIGH",
  "reason": "Contains 'final' + module mapping from syllabus"
}
```

---

## 🛠️ Dependencies

| Package | Purpose |
|---------|---------|
| **streamlit** | Web UI framework |
| **openai** | Whisper transcription + GPT-4o LLM + embeddings API |
| **langchain** | LLM orchestration and prompting framework |
| **langchain-openai** | OpenAI integration for LangChain |
| **langchain-community** | Vector store and text splitting utilities |
| **faiss-cpu** | In-memory vector similarity search (FAISS) |
| **PyPDF2** | Extract text from PDF syllabi |
| **gTTS** | Text-to-speech synthesis (free, offline-capable) |
| **python-dotenv** | Load environment variables from `.env` |

---

## 💰 Cost Estimate

Typical processing costs per lecture (10 minutes of audio):

| Operation | Cost/Qty | Notes |
|-----------|----------|-------|
| **Whisper** | $0.001 | Audio transcription |
| **Text Embeddings** | ~$0.0001 | Vectorizing ~30 syllabus chunks & transcript segments |
| **GPT-4o** | ~$0.01–$0.03 | Structured note generation (~2k–4k output tokens) |
| **gTTS** | Free | Text-to-speech synthesis (no API cost) |
| **Total** | ~$0.02 | Per 10-minute lecture (estimate) |

*Costs vary by lecture length, syllabus size, and API rate changes.*

---

## 📁 Project Structure

```
Audora/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT License
├── README.md              # This file
└── .venv/                 # Virtual environment (generated locally)
```

---

## 🎨 UI/UX Highlights

- **Dark Theme**: High-contrast color palette optimized for long study sessions
- **Typography**: Professional sans-serif (Inter) + monospace (DM Mono) for technical content
- **Responsive Layout**: Works on desktop, tablet, and mobile (though optimized for desktop)
- **Accessibility**:
  - ARIA labels on all interactive elements
  - Focus indicators for keyboard navigation
  - Semantic HTML structure
  - Screen reader friendly
  - TTS option for multilingual accessibility

---

## 🚨 Limitations & Known Issues

1. **API Key Required**: OpenAI API key is mandatory. Free trial credits work, but production use requires paid API access.
2. **FAISS In-Memory**: Large syllabi (>50MB) may consume significant RAM. For massive documents, chunk pre-processing is recommended.
3. **LLM Hallucinations**: While the syllabus grounding reduces hallucinations, GPT-4o may occasionally invent module names if the syllabus context is weak. Always review critical content.
4. **Audio Quality**: Whisper works best with clear audio. Heavy background noise may reduce transcription accuracy.
5. **Language Support (TTS)**: gTTS supports ~150 languages, but note quality varies. English, Spanish, and French have the best results.
6. **Session-Only Storage**: All data (transcript, notes, vectors) lives in memory for the current session. Refresh the page to clear.

---

## 🔐 Privacy & Security

- **API Key Handling**: Your OpenAI API key is **never stored**, **never logged**, and only transmitted over HTTPS to OpenAI endpoints.
- **Session Data**: All uploaded files, transcripts, and generated notes are stored in-memory for the current Streamlit session only. They are cleared when:
  - You refresh the browser tab
  - Close the tab
  - Restart the Streamlit server
- **No Analytics**: Audora does not track usage, collect telemetry, or phone home.
- **Local FAISS**: Your syllabus embeddings are computed locally and not sent to external services.

---

## 🐛 Troubleshooting

### "Missing dependencies" warning
**Solution**: Run the provided install command:
```bash
pip install openai langchain langchain-openai langchain-community faiss-cpu PyPDF2 gTTS streamlit
```

### Transcription returns empty
**Solutions**:
1. Check your OpenAI API key validity
2. Verify the audio file is a supported format (MP3, MP4, M4A, WAV)
3. Check OpenAI API quota/credits at https://platform.openai.com/account/billing/overview
4. Ensure audio file size is <25 MB (Whisper API limit)

### "Syllabus processing error"
**Solutions**:
1. Verify the PDF is text-extractable (not a scanned image)
2. Try a TXT file instead if PDF fails
3. Ensure the file is <50 MB
4. Check file encoding (UTF-8 recommended)

### Notes are generic/lack structure
**Solutions**:
1. Upload a course syllabus for better grounding
2. Ensure your lecture audio is clear (low background noise)
3. Try a different lecture if one returns poor results

### TTS audio is slow/garbled
**Solutions**:
1. Disable TTS if not needed (saves processing time)
2. Try a different target language
3. Check your internet connection (gTTS requires online access)

### FAISS index memory errors on large syllabi
**Solutions**:
1. Use a shorter syllabus excerpt if testing
2. Increase available RAM before running
3. Consider reducing the chunk size in `build_syllabus_vectorstore()` (line ~545)

---

## 📚 Technical Deep Dive

### Syllabus Vectorization Pipeline
1. **Text Splitting**: Syllabus is split into 600-token chunks with 100-token overlap to preserve topic boundaries.
2. **Embedding**: Each chunk is embedded with OpenAI's `text-embedding-3-small` model (~$0.02 per million tokens).
3. **FAISS Indexing**: Embeddings are stored in a FAISS flat index for fast approximate nearest-neighbor retrieval.
4. **Ground Truth Injection**: During LLM prompting, the top-8 most relevant syllabus chunks are injected as system context.

### Noise Gate (Content Filtering)
The system prompt (lines 300–365) instructs GPT-4o to classify and remove:
- Non-academic segments (greetings, admin notices, off-topic tangents)
- Filler words and repetition
- A count of filtered segments is returned for transparency

### Exam Radar Scoring
Exam hints are flagged based on:
1. **Presence of urgency keywords** in the transcript
2. **Semantic relevance** to course modules (via FAISS context)
3. **Confidence level** (HIGH for direct exam language, MEDIUM for implicit importance)

---

## 🤝 Contributing

We welcome contributions! Here are some ideas:
- [ ] Add support for video subtitles as input (instead of audio-only)
- [ ] Implement persistent storage (SQLite/PostgreSQL) for lecture history
- [ ] Add a quiz generator based on exam radar hints
- [ ] Integrate Anthropic's Claude 3.5 as an alternative LLM
- [ ] Support for slide deck (PDF) extraction and alignment
- [ ] Real-time transcription with streaming Whisper API
- [ ] Dark mode toggle (currently always dark)
- [ ] Lecture comparison tool (compare notes across multiple lectures)

To contribute:
1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License**—see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Om Shrivastava**  
GitHub: [@OmShrivastava19](https://github.com/OmShrivastava19)

---

## 🙏 Acknowledgments

- **OpenAI**: Whisper, Embeddings, and GPT-4o APIs
- **LangChain**: LLM orchestration and RAG framework
- **FAISS**: Meta's scalable similarity search library
- **Streamlit**: Rapid web app framework
- **gTTS**: Open-source text-to-speech

---

## 📞 Support

For issues, questions, or feature requests:
1. Check the [Troubleshooting](#-troubleshooting) section above
2. Open a GitHub Issue with:
   - Detailed error message and traceback
   - Steps to reproduce
   - Your Python version and OS
3. For OpenAI API issues, visit https://status.openai.com

---

**Made with ❤️ for students who want smarter, faster study notes.**
