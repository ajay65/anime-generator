
---

# 🎬 Anime Generator

Create professional, Japanese-style anime videos **locally** from a single `story.json`.
The script automatically generates **anime images**, **keeps characters consistent**, assigns **natural neural voices** (with slangs/dialects), overlays **subtitles**, mixes **BGM/SFX**, applies **camera effects**, and exports a final **MP4**.

---

## ✨ Features (What the script does)

* 🎨 **Anime image generation** (local): Stable Diffusion via **diffusers** (anime checkpoints)
* 🧑‍🎨 **Character consistency**: per-character seed + prompt templates (+ optional IP-Adapter/LoRA if you provide refs)
* 🗣️ **Voices with edge-tts**:

  * Automatic voice assignment per character (consistent within a run)
  * Default spoken language **Hindi**, supports **Hindi/English/Japanese**
  * Optional slang transforms: **Mumbaiya, Haryanvi, Bihari, UP**
* 🗨️ **Subtitles**: auto-translated (default overlay in **English**) via **deep-translator**
* 🎵 **BGM**: auto-picked by scene mood (or specify per scene)
* 🔊 **SFX**: timed/ambient overlays (sword clash, footsteps, explosion, etc.)
* 🎥 **Camera effects**: zoom, fades, dark/mystery tone, jitter for action
* ⏱️ **Duration control** per scene (+ fight mood auto-extension)
* 🖼️ **Subtitle rendering** on video (MoviePy, ImageMagick backend)
* 🎬 **Final export** to `outputs/anime_output.mp4`

---

## 🧩 How it works (High-level pipeline)

1. **Parse `story.json`** → scenes, dialogues, moods, sfx, duration.
2. **Image generator** (diffusers + anime checkpoint)

   * Builds **backgrounds** and **characters** per scene
   * Uses per-character **seed + prompt template** for consistency
   * (Optional) If you provide a reference image later, it can use **IP-Adapter** for stronger consistency—no training required.
3. **Dialogue engine**

   * Applies **slang dialect** (Mumbaiya/Bihari/UP/Haryanvi) for Hindi text
   * Synthesizes **voice** with **edge-tts** (neural, natural)
   * Automatically picks/sticks a unique voice per character (within the run)
4. **Subtitles**

   * Auto-translate to **English** (overlay), plus **Hindi/Japanese** text available if needed
5. **Audio mix**

   * Auto BGM based on mood (+ optional per scene override)
   * Layer SFX (ambient + timed)
   * Loop/trim to fit scene duration
6. **Video assembly**

   * Apply camera FX (zoom/fade/mystery tone/jitter)
   * Composite frame + subtitles + audio
   * Concatenate scenes → export MP4

---

## 🖥️ Requirements

* **Windows 11**
* **Python 3.11** (use a virtual environment)
* **RAM:** 16–32 GB recommended
* **GPU (optional but recommended):** NVIDIA for fast image generation

  > CPU works but is slow. You can start CPU-only, then switch to GPU later.

---

## 📁 Project Structure

```
anime_generator/
│── main.py
│── story.json
│── assets/
│   ├── bgm/     # background music (or auto-picked by mood)
│   └── sfx/     # sound effects (footsteps, sword, explosion...)
│── outputs/     # final videos
│── temp/        # generated frames/voices/intermediates
│── requirements.txt
│── README.md
```

---

## 🧪 Example Inputs

* `story.json`: drives **everything** (scenes, characters, moods, dialogues, sfx/timing)
* **You don’t need to collect images**: the script generates anime-style frames from prompts.
  (Optional later: add 1–2 character reference images to supercharge consistency via IP-Adapter.)

---

## 🚀 Quick Start

### 1) Create & activate virtual environment (Python 3.11)

```bat
cd anime_generator
python -m venv venv
venv\Scripts\activate
```

If your global Python isn’t 3.11, install 3.11 from the official site and then create the venv.

---

## 🔧 Step 2 – Install Dependencies (what & why)

Install Python packages:

```bat
pip install -r requirements.txt
```

**What each package is for:**

| Package           | Why we install it / What it does                                      |
| ----------------- | --------------------------------------------------------------------- |
| `diffusers`       | Stable Diffusion pipelines (image generation, anime checkpoints).     |
| `transformers`    | Model config/utilities required by diffusers.                         |
| `torch`           | The AI runtime backend (CPU/GPU).                                     |
| `safetensors`     | Safe, fast model weight format used by many SD models.                |
| `edge-tts`        | **Microsoft neural TTS** (natural voices) for Hindi/English/Japanese. |
| `deep-translator` | Subtitles auto-translation (default to English).                      |
| `moviepy`         | Video assembly, audio mixing, subtitle rendering.                     |
| `pillow==9.5.0`   | Image ops; **pinned** to avoid `ANTIALIAS` breaking with MoviePy.     |
| `imageio`         | Required by MoviePy for media I/O.                                    |
| `numpy`           | Numerical ops, arrays.                                                |
| `tqdm`            | Optional progress bars.                                               |

> **System tools required by MoviePy TextClip**
>
> * **FFmpeg** → audio/video encoding/decoding
> * **ImageMagick** → text rendering for subtitles (MoviePy’s `TextClip` uses it on Windows)

### Install FFmpeg (choose one):

* **winget** (Windows package manager):

  ```bat
  winget install Gyan.FFmpeg
  ```
* **Chocolatey**:

  ```bat
  choco install ffmpeg
  ```
* **Manual**: Download static build from ffmpeg.org and add `bin` to PATH.

### Install ImageMagick:

* Download from: [https://imagemagick.org/script/download.php#windows](https://imagemagick.org/script/download.php#windows)
  During setup:

  * ✅ Check **“Install legacy utilities”**
  * ✅ Check **“Install FFmpeg delegates”** if offered
* Note the install path (e.g. `C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe`)
* The script sets this path via:

  ```python
  from moviepy.config import change_settings
  change_settings({"IMAGEMAGICK_BINARY": r"C:\Path\To\ImageMagick\magick.exe"})
  ```

If your path is different, update it in **`main.py`**.

---

## 📥 Step 3 – Download Models (what & why)

We use **anime-tuned Stable Diffusion** checkpoints from Hugging Face.
Good starter checkpoints:

* **Anything v4.0** (`andite/anything-v4.0`) – widely used anime model
* (Optional later) **LoRA/IP-Adapter** – for stronger character consistency if you add a reference image

### Hugging Face setup

1. Create account: [https://huggingface.co/join](https://huggingface.co/join)
2. (If model requires) Accept license on its page.
3. Login locally:

   ```bat
   huggingface-cli login
   ```
4. First run will **auto-download** the model to your HF cache:

   ```
   C:\Users\YOURNAME\.cache\huggingface\hub
   ```

   You can change cache location by setting `HF_HOME`.

> **Why this is needed**
> The script calls diffusers with a model like `andite/anything-v4.0`. Diffusers fetches it the first time and caches it for future runs.

---

## ▶️ Step 4 – First Run & Verification (full, detailed)

1. Put a **test `story.json`** (the example you got from me earlier that exercises all features) in the project root.

2. Ensure assets structure exists (optional if relying entirely on auto BGM):

```
assets/
  bgm/  (place any .mp3; or rely on auto pick)
  sfx/  (footsteps.mp3, sword_clash.mp3, explosion.mp3, thunder.mp3, etc.)
```

3. Activate venv and run:

```bat
venv\Scripts\activate
python main.py story.json
```

4. On first run, you’ll see:

* diffusers downloading the anime model (only once)
* MoviePy rendering scenes
* edge-tts generating voices
* Final video at: `outputs/anime_output.mp4`

5. **Check voices**

   * The script **auto-assigns** a unique voice per character (consistent within the run).
   * To force a specific voice, set it per character in `story.json` (e.g., `voice_hint: "ja-JP-NanamiNeural"`).

---

## 🗣️ Voice System (edge-tts)

* Uses **Microsoft Neural TTS** (local client; requires internet).
* Default spoken language = **Hindi** (e.g., `hi-IN-MadhurNeural`).
* Supported languages in the script: **Hindi, English, Japanese**.
* **Auto assignment**: Each new character gets a unique voice from a curated list; the same character keeps the same voice in all scenes (within a run).
* **Slang/Dialect**: `apply_slang()` transforms the text for Hindi variants:

  * `hindi_mumbaiya`, `hindi_bihari`, `hindi_up`, `hindi_haryanvi`

**Common voice examples you can use in `story.json`:**

* Hindi: `hi-IN-MadhurNeural`, `hi-IN-SwaraNeural`
* English (US): `en-US-GuyNeural`, `en-US-AriaNeural`
* Japanese: `ja-JP-NanamiNeural`, `ja-JP-KeitaNeural`

---

## 📜 `story.json` Schema (what every field does)

```jsonc
{
  "video": {
    "width": 1280,
    "height": 720,
    "fps": 24,
    "default_spoken_language": "hi",     // default voice language (hi/en/ja)
    "default_subtitle_language": "en",   // overlay subtitle language
    "model": "andite/anything-v4.0"      // anime SD checkpoint (diffusers)
  },
  "characters": [
    {
      "name": "Hero",
      "seed": 123456,                    // per-character seed for visual consistency
      "prompt": "heroic teen swordsman, spiky black hair, red scarf, anime style",
      "negative_prompt": "blurry, deformed, lowres",
      "voice_hint": "hi-IN-MadhurNeural",// optional fixed voice
      "slang": "hindi_mumbaiya"          // optional dialect for this character
    }
    // add more characters...
  ],
  "scenes": [
    {
      "id": 1,
      "description": "Dawn over a misty valley. Hero draws his sword.",
      "mood": "epic",                    // happy/sad/romantic/epic/angry/mystery/neutral
      "duration": 7,
      "bgm": "epic.mp3",                 // optional; if omitted, auto-picked by mood
      "sfx": ["soft_breeze.mp3"],        // ambient sfx
      "sfx_timed": [                     // timed sfx
        { "file": "sword_clash.mp3", "time": 4.1 }
      ],
      "camera": {                        // optional per-scene camera fx
        "zoom": true,
        "fade": true,
        "darken": false,
        "shake": true
      },
      "dialogue": [
        {
          "character": "Hero",
          "lang": "hi",                  // hi/en/ja
          "voice": "hindi_mumbaiya",     // or specific edge-tts voice name using voice_hint above
          "text": "Yeh ladai khatam nahi hui, abhi apun ka khel shuru hua hai!"
        }
      ]
    }
    // more scenes...
  ]
}
```

---

## 🎶 Audio Handling (BGM/SFX)

* **BGM**: If `bgm` missing, the script picks one based on `mood`.
* **Loop/Trim**: All audio is trimmed/looped to match the scene duration, so music never ends early.
* **SFX**:

  * `sfx`: ambient, starts near t=0 and loops/extends
  * `sfx_timed`: fires at exact timestamps (e.g., sword clash at 4.1s)
* **Fight moods** (`angry`, `epic`) auto-extend duration a bit and inject extra battle SFX (if available).

---

## 🎥 Camera Effects

* `epic`, `angry`: subtle zoom + fade in/out
* `mystery`: darker tone
* `sad`: longer fades
* Optional `shake` for action scenes

---

## 🧠 Character Consistency (no training required)

* **Default**: Uses **per-character seed + prompt template** → consistent hair/clothes/colors across scenes.
* **Optional (later)**: Add a single face or character reference image and enable **IP-Adapter** locally to lock identity even harder (no LoRA training needed). The README keeps you CPU-friendly; you can add this later when ready.

---

## 🛠️ Troubleshooting & Fixes

**1) “MoviePy Error… ImageMagick not installed” or TextClip fails**

* Install ImageMagick and ensure `magick.exe` path matches the one set in `main.py`:

  ```python
  change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})
  ```

**2) “AttributeError: PIL.Image has no attribute ANTIALIAS”**

* Use **Pillow 9.5.0** (pinned in requirements). If you upgraded by accident:

  ```bat
  pip install "pillow==9.5.0" --upgrade --force-reinstall
  ```

**3) “FFmpeg not found”**

* Install via `winget install Gyan.FFmpeg` or add `ffmpeg\bin` to PATH.

**4) First run is slow**

* Model downloads happen once. Subsequent runs load from cache.

**5) CPU too slow**

* Consider adding an NVIDIA GPU later. For now, reduce image resolution (e.g., 768×432) in `video.width/height` to speed up.

**6) Voices sound too similar**

* Add `voice_hint` per character (e.g., `ja-JP-KeitaNeural`, `en-US-GuyNeural`, `hi-IN-SwaraNeural`).

---

## 📦 `requirements.txt` (why pinned)

```
torch               # PyTorch backend (CPU/GPU)
diffusers           # Stable Diffusion pipelines
transformers        # model configs, tokenizer utils
safetensors         # serialized weights format
edge-tts            # Microsoft neural TTS (natural voices)
deep-translator     # subtitle translation
moviepy             # video editing
pillow==9.5.0       # image handling (pinned for MoviePy compatibility)
imageio             # media IO backend
numpy               # array math
tqdm                # progress bars (optional)
```

**Why pin Pillow?** MoviePy’s `TextClip` still references the `ANTIALIAS` constant removed in Pillow ≥10. Pinning avoids runtime errors on Windows.

---

## 🏃 Run

```bat
venv\Scripts\activate
python main.py story.json
```

Result: `outputs/anime_output.mp4`

---

## 🔒 Privacy & Offline Notes

* Image generation (diffusers/torch) is **local**.
* edge-tts requires network access to Microsoft’s TTS service for voice synthesis.
* If you need fully offline TTS later, we can swap to an offline model (quality trade-offs).

---

## 🧭 What to customize later

* **Model** (`video.model`): try other anime checkpoints for different looks
* **IP-Adapter/LoRA**: add reference images for stronger identity locking (still no training)
* **Voice list**: expand/curate the pool of edge-tts voices used by auto-assignment
* **BGM/SFX**: drop your own assets into `assets/bgm` and `assets/sfx`

---

## ✅ Recap of Features Covered

* Anime image gen (diffusers)
* Character consistency (seed + prompt templates; optional IP-Adapter later)
* Voices (edge-tts), auto-assigned + consistent per character, Hindi default
* Slangs/dialects (Hindi variants)
* Subtitles (auto-translated; English overlay by default)
* Auto BGM by mood + SFX timed/ambient
* Camera effects (zoom/fade/mystery/shake)
* Duration control + fight mood extensions
* Final MP4 assembly with MoviePy

---

