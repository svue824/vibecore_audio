<p align="center">
  <img src="assets/vibecore_audio_logo.png" width="220">
</p>
<h1 align="center">VibeCore Audio 🎧</h1>
<p align="center">
  Modern multi-track desktop audio editor built with Python + Qt (PySide6).
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt&logoColor=white">
  <img src="https://img.shields.io/badge/Status-Active%20Prototype-0A0A0A">
</p>

---

## 🚀 Download (Recommended)

No Python required.

👉 **Download the latest Windows build here:**  
https://github.com/svue824/vibecore_audio/releases

### How to Run

1. Download `VibeCoreAudio.exe`
2. Double-click to launch
3. If Windows shows a security warning:
   - Click **More info**
   - Click **Run anyway**

That's it.

---

## 🎛 Features

- Multi-track project workflow  
- Record audio into tracks  
- Playback individual tracks or full project mix  
- Timeline + waveform editing  
- Volume / mute per track  
- Save & open projects  
- Export mix (UI wired)

---

## 🛠 Developer Setup

### 1. Clone Repository
```bash
git clone https://github.com/svue824/vibecore_audio.git
cd vibecore_audio
```

### 2. Create Virtual Environment

**Windows**
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -e .
```

### 4. Launch the App
```bash
vibecore
```

If running without editable install:
```bash
set PYTHONPATH=src   # Windows
# export PYTHONPATH=src   # macOS/Linux
python -m audio_editor.ui.main_window
```

---

## 🧪 Development Workflow

**Run Tests:**
```bash
pytest
```

**Format Code:**
```bash
black src tests
```

**Lint:**
```bash
ruff check src tests
```

**Type Check:**
```bash
mypy src
```

---

## 🏗 Build Executable (Windows)
```bash
pyinstaller --name VibeCoreAudio --onefile --windowed --icon=src/assets/vibecore_audio.ico src/audio_editor/ui/main_window.py
```

Output:
```
dist/VibeCoreAudio.exe
```

---

## 🧠 Architecture
```
src/audio_editor/
  domain/          Core entities (Project, AudioTrack)
  use_cases/       Application actions
  services/        Audio engine integration
  ui/              PySide6 desktop UI
```

---

## 📌 Project Entry Point

Defined in `pyproject.toml`:
```toml
vibecore = "audio_editor.ui.main_window:main"
```
