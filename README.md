
# 🎬 AI Anime Generator

Generate **anime-style videos** from a simple story JSON — complete with **consistent characters, realistic voices, subtitles, BGM, SFX, and camera effects**.
Runs **fully free** using the **Stable Horde API** (community distributed GPU network) + **Microsoft Edge Neural TTS** for voices.

---

## ✨ Features

* 🧑‍🎨 **Character consistency**

  * Each character has a **unique seed** so their face remains consistent across scenes.
  * Optional: provide a **reference image** per character (IP-Adapter style).

* 🗣️ **Voices (Edge-TTS)**

  * Automatic **voice assignment per character** (consistent for the whole run).
  * Default spoken language **Hindi**; supports **English, Hindi, Japanese**.
  * Regional slangs: **Mumbaiya, Haryanvi, Bihari, UP**.
  * Falls back to **gTTS** if Edge-TTS fails.

* 🗨️ **Subtitles**

  * Auto-translated via `deep-translator`.
  * Default overlay in **English**, optional Hindi/Japanese.

* 🎵 **Background Music (BGM)**

  * Auto-picked from assets by **scene mood**.
  * Can be overridden in story JSON.

* 🔊 **Sound Effects (SFX)**

  * Add ambient SFX per scene.
  * Add **timed SFX** (e.g., sword clash at 2s, explosion at 4s).

* 🎥 **Camera effects**

  * Zoom, fade-in/out, color grading for mystery scenes, jitter for action scenes.

* ⏱️ **Scene duration control**

  * Per-scene duration.
  * Auto-extends for **epic/fight scenes**.

* 🖼️ **Subtitle rendering**

  * Overlaid text at bottom (MoviePy + ImageMagick).

* 🎬 **Final export**

  * Video saved to `outputs/anime_output.mp4`.

---

## 📂 Project Structure

```
anime-generator/
│── main.py                 # Main script
│── story.json              # Input story file
│── assets/
│   ├── bgm/                # Background music files
│   └── sfx/                # Sound effects
│── outputs/                # Final video output
│── temp/                   # Temporary images/audio
│── requirements.txt        # Python dependencies
│── README.md               # Documentation
```

---

## ⚙️ Installation

### 1. Clone repo & setup environment

```powershell
git clone https://github.com/yourname/anime-generator.git
cd anime-generator

# create venv
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

Key packages used:

* `edge-tts` → Microsoft Edge Neural TTS
* `gTTS` → fallback voice synthesis
* `moviepy` → video editing & effects
* `Pillow` → fallback placeholder image generator
* `deep-translator` → subtitles (Google Translate backend)
* `requests` → Stable Horde API calls

---

## 🖼️ Stable Horde Setup (Free Anime Image Generation)

We use **Stable Horde** (distributed GPU network, free).

### Step 2 — Get API key

1. Go to [Stable Horde](https://stablehorde.net/register).
2. Sign up (free).
3. Copy your API key from dashboard.

### Step 3 — Configure environment

Create `.env` file in project root:

```ini
HORDE_API_KEY=your_api_key_here
```

### Step 4 — Anime Models

Stable Horde automatically routes to available **anime-tuned models** such as:

* **Anything V5**
* **Counterfeit-V3**
* **AOM3**

We don’t need to download models — Horde provides them free.

Character consistency:

* Script uses **per-character seeds** + optional **reference image**.
* Add references in `CHARACTER_REGISTRY` inside `main.py`.

Example:

```python
CHARACTER_REGISTRY = {
    "hero": {
        "voice": "hi-IN-MadhurNeural",
        "seed": 123456,
        "ref_image": "assets/characters/hero.png"
    }
}
```

If no `ref_image`, seed ensures consistency.

---

## 📝 Story Format

`story.json` example:

```json
{
  "scenes": [
    {
      "description": "A young hero stands on a mountain, looking at the sunset.",
      "duration": 8,
      "mood": "epic",
      "dialogue": [
        {
          "character": "Hero",
          "text": "Yeh sirf shuruaat hai!",
          "lang": "hi",
          "slang": "hindi_mumbaiya"
        }
      ],
      "sfx": ["wind.mp3"],
      "sfx_timed": [{"file": "sword_clash.mp3", "time": 3}]
    },
    {
      "description": "The villain appears with glowing red eyes.",
      "duration": 6,
      "mood": "angry",
      "dialogue": [
        {
          "character": "Villain",
          "text": "Main tumhe mita dunga!",
          "lang": "hi"
        }
      ]
    }
  ]
}
```

---

## ▶️ Run

```powershell
python main.py story.json
```

Result:

* Generates anime-style images per scene (Stable Horde API).
* Keeps characters **consistent** (seed + ref images).
* Assigns **voices** to characters.
* Adds **BGM, SFX, subtitles, camera effects**.
* Exports `outputs/anime_output.mp4`.

---

## 🚀 Roadmap / Extensions

* [ ] Add lip-sync with **Wav2Lip**.
* [ ] More anime-specific Horde models.
* [ ] Local Stable Diffusion (if you add a GPU later).

---
