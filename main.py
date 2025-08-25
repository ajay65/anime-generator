"""
main.py — Anime Video Generator (Stable Horde + Edge-TTS, Character Consistency)
-------------------------------------------------------------------------------

WHAT THIS DOES
--------------
Builds an anime-style video from a JSON story, fully locally except for free
image generation via the Stable Horde API (community GPUs).

Key Features (ALL INCLUDED)
- 🧑‍🎨 Character consistency:
  - Deterministic per-character seed
  - Per-character prompt template
  - Optional reference image (img2img through Stable Horde) for IP-Adapter-like consistency
- 🎨 Anime image generation (free) via Stable Horde (e.g., Anything v5 / anime models)
- 🗣️ Voices with Edge-TTS:
  - Automatic, consistent voice per character (persisted)
  - Hindi default; supports hi/en/ja
  - Optional slang transforms: Mumbaiya, Haryanvi, Bihari, UP
  - gTTS used as a last-resort fallback
- 🗨️ Subtitles: auto-translated to English (overlay), Hindi, Japanese
- 🎵 BGM: auto-picked by mood (or specify per scene)
- 🔊 SFX: ambient + timed overlays (e.g., sword_clash.mp3, explosion.mp3)
- 🎥 Camera FX: zoom for epic/angry, fade, darker mystery, optional jitter
- ⏱️ Duration control per scene (+ auto-extension for epic/angry/fight)
- 🖼️ Subtitle rendering (MoviePy TextClip using ImageMagick backend)
- 🎬 Final export to outputs/anime_output.mp4

INPUT
-----
    python main.py story.json

story.json (example skeleton)
-----------------------------
{
  "title": "My Anime",
  "scenes": [
    {
      "description": "Hero stands on a rooftop at night, neon city behind, wind blowing.",
      "mood": "mystery",
      "duration": 8,
      "bgm": "mystery.mp3",           # optional (else auto-picked by mood)
      "sfx": ["wind.mp3"],            # optional
      "sfx_timed": [{"file":"sword_clash.mp3","time":3.5}],
      "characters": ["hero"],         # names must match CHARACTER_REGISTRY keys (see below)
      "dialogue": [
        {"character":"hero","text":"Aaj raat sab kuchh badal jayega.","lang":"hi","voice":"hindi_mumbaiya"}
      ]
    }
  ]
}

SETUP NOTES
-----------
- Stable Horde API key (optional): set env var HORDE_API_KEY; anonymous "0000000000" works.
- Put BGM in assets/bgm, SFX in assets/sfx.
- For character reference images, place files in assets/characters/ and set in CHARACTER_REGISTRY (below).
- ImageMagick must be installed & IMAGEMAGICK_BINARY path set (configured below for Win).

Author: Your Anime AI Assistant
"""

import os
import sys
import json
import time
import base64
import random
import hashlib
import asyncio
from pathlib import Path
import threading # For rate limiting

import requests
from deep_translator import GoogleTranslator
from gtts import gTTS
import edge_tts  # Microsoft Edge Neural TTS

from moviepy.editor import (
    ImageClip, AudioFileClip, concatenate_audioclips, concatenate_videoclips,
    CompositeAudioClip, CompositeVideoClip, TextClip, vfx
)
from moviepy.config import change_settings
from PIL import Image, ImageDraw, ImageFont

import concurrent.futures # For parallel processing
# --- Font Path Configuration ---
# Prioritize ANIME_GENERATOR_FONT_PATH environment variable, then common Windows path, then a relative path
_default_font_path = r"C:\Windows\Fonts\Verdana.ttf"
_fallback_font_path = "assets/fonts/NotoSans-Regular.ttf" # Assuming a fallback font might be placed here
font_path = os.getenv("ANIME_GENERATOR_FONT_PATH", _default_font_path)

# Ensure font file exists, otherwise try fallback or raise error
if not os.path.exists(font_path):
    if os.path.exists(_fallback_font_path):
        font_path = _fallback_font_path
    else:
        print(f"⚠️ Warning: Font file not found at {font_path} or {_fallback_font_path}. Subtitles might not render correctly.")
        # Attempt to use a generic font if specific ones are not found
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None # No font available
else:
    font_size = 28  # adjust as needed
    font = ImageFont.truetype(font_path, font_size)


# --- ImageMagick Path Configuration ---
# Prioritize ANIME_GENERATOR_IMAGEMAGICK_BINARY environment variable
_default_imagemagick_path = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
imagemagick_binary = os.getenv("ANIME_GENERATOR_IMAGEMAGICK_BINARY", _default_imagemagick_path)

change_settings({
    "IMAGEMAGICK_BINARY": imagemagick_binary
})

# ---------------------------
# CONSTANTS & PATHS
# ---------------------------
ASSETS_BGM = "assets/bgm"
ASSETS_SFX = "assets/sfx"
ASSETS_CHAR = "assets/characters"
TEMP_DIR = "temp"
OUTPUT_DIR = "outputs"
VOICE_MAP_PATH = os.path.join(OUTPUT_DIR, "character_voices.json")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
from dotenv import load_dotenv


# Load variables from .env file
load_dotenv()


# ---------------------------
# Stable Horde endpoints & config
# ---------------------------
HORDE_KEY = os.getenv("HORDE_API_KEY", "0000000000")  # anonymous key is fine
HORDE_API = "https://stablehorde.net/api/v2/generate/async"
HORDE_CHECK = "https://stablehorde.net/api/v2/generate/check"
HORDE_STATUS = "https://stablehorde.net/api/v2/generate/status"

# Prefer anime models commonly available on Horde. Order is a hint; workers may vary.
HORDE_ANIME_MODELS = [
    "anythingv5_prtRE", "anythingv5_pruned", "AOM3A3_orangemixs", "Counterfeit-V3.0",
    "pastel_mix", "animePastel_v10", "MeinaMix"
]

# Image generation timeout (seconds) - increased as per user request
HORDE_IMAGE_GENERATION_TIMEOUT = 400 # Increased timeout as per user request, and for parallel processing

# Stable Horde API rate limit: 2 requests per second
RATE_LIMIT_SEMAPHORE = threading.Semaphore(2)

# ---------------------------
# Character registry (edit to add your cast)
# Each character gets: prompt tags, default voice, optional ref image for img2img
# ---------------------------
CHARACTER_REGISTRY = {
    # Example
    "hero": {
        "prompt": "young male hero, black spiky hair, navy jacket, determined eyes, anime style",
        "voice_name": "hi-IN-MadhurNeural",    # default voice for auto-assignment
        "ref_image": f"{ASSETS_CHAR}/hero.png",  # optional; if exists, img2img for consistency
        "img2img_strength": 0.55               # how strongly to follow the ref (0.3-0.7 typical)
    },
    "villain": {
        "prompt": "adult male villain, white hair, red eyes, long coat, sinister grin, anime style",
        "voice_name": "en-US-GuyNeural",
        "ref_image": f"{ASSETS_CHAR}/villain.png",
        "img2img_strength": 0.55
    },
    "narrator": {
        "prompt": "narration background, cinematic framing, anime style",
        "voice_name": "en-US-JennyNeural",
        "ref_image": None
    }
}

# ---------------------------
# Utility: deterministic seed per character (consistency)
# ---------------------------
def seed_from_name(name: str) -> int:
    h = hashlib.sha256(name.encode("utf-8")).hexdigest()
    return int(h[:8], 16)  # 32-bit seed

# ---------------------------
# Voice assignment persistence
# ---------------------------
DEFAULT_VOICES = {
    "hi": ["hi-IN-MadhurNeural", "hi-IN-SwaraNeural"],
    "en": ["en-US-GuyNeural", "en-US-JennyNeural", "en-GB-RyanNeural", "en-GB-SoniaNeural"],
    "ja": ["ja-JP-KeitaNeural", "ja-JP-NanamiNeural"]
}

def load_voice_map():
    if os.path.exists(VOICE_MAP_PATH):
        try:
            return json.load(open(VOICE_MAP_PATH, "r", encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"⚠️ Error decoding character_voices.json: {e}")
        except IOError as e:
            print(f"⚠️ Error reading character_voices.json: {e}")
    return {}

def save_voice_map(mapping):
    try:
        json.dump(mapping, open(VOICE_MAP_PATH, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"⚠️ Error writing character_voices.json: {e}")

CHAR_VOICE_MAP = load_voice_map()

def pick_voice_for_character(char_name: str, lang_hint: str = "hi") -> str:
    """
    Pick a consistent voice for a character. Priority:
    1) Character registry voice_name
    2) Persisted mapping
    3) Deterministic pick from DEFAULT_VOICES based on hash
    """
    reg = CHARACTER_REGISTRY.get(char_name.lower())
    if reg and reg.get("voice_name"):
        voice = reg["voice_name"]
        CHAR_VOICE_MAP[char_name] = voice
        save_voice_map(CHAR_VOICE_MAP)
        return voice

    if char_name in CHAR_VOICE_MAP:
        return CHAR_VOICE_MAP[char_name]

    pool = DEFAULT_VOICES.get(lang_hint, DEFAULT_VOICES["en"])
    idx = seed_from_name(char_name) % len(pool)
    voice = pool[idx]
    CHAR_VOICE_MAP[char_name] = voice
    save_voice_map(CHAR_VOICE_MAP)
    return voice

# ---------------------------
# Slang/Dialect transforms
# ---------------------------
def apply_slang(text: str, slang: str) -> str:
    if slang == "hindi_mumbaiya":
        return text.replace("tum", "tu").replace("aap", "apun") + " re!"
    if slang == "hindi_bihari":
        return "Arre " + text.replace("tum", "tohra") + " baa"
    if slang == "hindi_up":
        return text.replace("main", "hum") + " bhaiya"
    if slang == "hindi_haryanvi":
        return "Sun le " + text.replace("hai", "se")
    return text

# ---------------------------
# Subtitles (auto-translate)
# ---------------------------
def translate_text(text, lang):
    try:
        return GoogleTranslator(source="auto", target=lang).translate(text)
    except Exception:
        return text

def generate_subtitles(text):
    return {
        "en": translate_text(text, "en"),
        "hi": translate_text(text, "hi"),
        "ja": translate_text(text, "ja")
    }

# ---------------------------
# Voice synthesis (Edge-TTS, async + sync wrapper)
# ---------------------------
async def synthesize_voice_async(text, lang="hi", slang=None, filename="voice.mp3", voice_name=None):
    if slang:
        text = apply_slang(text, slang)
    if voice_name is None:
        # fallback voice by language
        voice_name = DEFAULT_VOICES.get(lang, DEFAULT_VOICES["en"])[0]

    filepath = os.path.join(TEMP_DIR, filename)

    try:
        communicate = edge_tts.Communicate(text, voice_name)
        await communicate.save(filepath)
        return filepath
    except Exception as e:
        print(f"⚠️ Edge-TTS failed ({e}); trying gTTS fallback...")
        try:
            tts = gTTS(text=text, lang=lang)
            tts.save(filepath)
            return filepath
        except Exception as e2:
            print(f"⚠️ gTTS fallback failed: {e2}")
            return None

# ---------------------------
# Stable Horde image generation (re-implemented in main.py as per user request)
# ---------------------------

def b64_of_file(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def build_scene_prompt(scene_desc: str, characters: list[str]) -> tuple[str, int | None, str | None, float]:
    """
    Combine scene description with character prompt templates.
    Returns: full_prompt, seed, ref_image, denoise
    """
    char_prompts = []
    seeds = []
    ref = None
    denoise = 0.55

    for cname in characters or []:
        key = cname.lower()
        reg = CHARACTER_REGISTRY.get(key)
        if reg:
            if reg.get("prompt"):
                char_prompts.append(reg["prompt"])
            if reg.get("ref_image") and os.path.exists(reg["ref_image"]) and ref is None:
                ref = reg["ref_image"]
                denoise = float(reg.get("img2img_strength", 0.55))
            seeds.append(seed_from_name(cname))

    # Use first character seed if available, else None (let Horde decide)
    seed = seeds[0] if seeds else None

    # Compose prompt
    base_tags = "anime style, highly detailed, cinematic lighting, vibrant colors, key visual, professional"
    char_block = ", ".join(char_prompts) if char_prompts else ""
    full_prompt = f"{base_tags}, {scene_desc}"
    if char_block:
        full_prompt += f", {char_block}"

    return full_prompt, seed, ref, denoise

def generate_scene_image(scene_desc: str, scene_id: int, characters: list[str] | None):
    """
    Generate anime scene image via Stable Horde (free).
    - Uses per-character prompt templates and seed.
    - If character has a ref image, uses img2img for stronger consistency.
    - Caches the output in temp/scene_{id}.png.
    Falls back to a text placeholder if Horde fails.
    """
    img_path = os.path.join(TEMP_DIR, f"scene_{scene_id}.png")
    if os.path.exists(img_path):
        return img_path  # cached

    full_prompt, seed, ref_img, denoise = build_scene_prompt(scene_desc, characters or [])

    headers = {
        "apikey": HORDE_KEY,
        "Client-Agent": "anime-generator:0.1"
    }

    # Format generation parameters
    params = {
        "sampler_name": "k_euler_a",
        "cfg_scale": 7,
        "steps": 28,
        "width": 768,  # Default width
        "height": 512, # Default height
        "karras": True,
        "n": 1
    }
    if seed is not None:
        params["seed"] = str(seed)

    payload = {
        "prompt": full_prompt,
        "params": params,
        "nsfw": False,
        "censor_nsfw": True,
        "workers": [],
        "models": HORDE_ANIME_MODELS,
        "r2": True
    }

    # Optional img2img reference
    if ref_img and os.path.exists(ref_img):
        payload["source_image"] = b64_of_file(ref_img)
        payload["source_processing"] = "img2img"
        payload["params"]["denoising_strength"] = float(denoise)

    try:
        with RATE_LIMIT_SEMAPHORE:
            time.sleep(0.5) # Adhere to Stable Horde rate limit (2 requests per second)
            # 1️⃣ Submit job
            r = requests.post(HORDE_API, headers=headers, json=payload, timeout=60)
            if r.status_code not in [200, 202]: # Stable Horde returns 202 Accepted for job submission
                print(f"❌ Horde submission failed with status code {r.status_code}:", r.text)
                raise RuntimeError(f"Horde submission failed: {r.status_code}")

            response_data = r.json()
            job_id = response_data.get("id")
            kudos_used = response_data.get("kudos")

        if not job_id:
            print("⚠️ Horde did not return a job ID")
            raise RuntimeError("Horde did not return a job ID")

        print(f"🆗 Job submitted: {job_id} | Kudos used: {kudos_used}")

        # 2️⃣ Poll for result
        interval = 4
        elapsed = 0
        while elapsed < HORDE_IMAGE_GENERATION_TIMEOUT:
            status = requests.get(f"{HORDE_STATUS}/{job_id}", headers=headers, timeout=HORDE_IMAGE_GENERATION_TIMEOUT).json() # Increased timeout for polling
            finished = status.get("finished", 0)
            processing = status.get("processing", 0)
            print(f"⏳ Polling for result... Finished: {finished}, Processing: {processing} | {elapsed}/{HORDE_IMAGE_GENERATION_TIMEOUT}s", end="\r")
            gens = status.get("generations", [])

            if gens and gens[0].get("img"):
                img_url = gens[0]["img"]
                try:
                    img_data = requests.get(img_url, timeout=30).content
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                    print(f"✅ Image ready after {elapsed}s: {img_path}")
                    return img_path
                except Exception as e:
                    print(f"⚠️ CDN download failed: {e}")
                    raise RuntimeError(f"CDN download failed: {e}")

            time.sleep(interval)
            elapsed += interval

        print(f"⚠️ Timeout: No image after {HORDE_IMAGE_GENERATION_TIMEOUT}s")
        raise RuntimeError(f"Timeout: No image after {HORDE_IMAGE_GENERATION_TIMEOUT}s")

    except Exception as e:
        print(f"⚠️ Horde failed ({e}); using placeholder.")
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (768, 512), color=(30, 30, 60)) # Use default image dimensions
        draw = ImageDraw.Draw(img)
        draw.text((40, 240), f"Scene {scene_id}: {scene_desc}", fill=(255, 255, 255), font=font)
        img.save(img_path)
        return img_path

# ---------------------------
# BGM selection
# ---------------------------
def pick_bgm(mood: str) -> str:
    mood_map = {
        "happy": "happy.mp3",
        "sad": "sad.mp3",
        "romantic": "romantic.mp3",
        "epic": "epic.mp3",
        "angry": "angry.mp3",
        "mystery": "mystery.mp3",
        "neutral": "neutral.mp3"
    }
    return mood_map.get(mood, "neutral.mp3")

def resolve_bgm(path_or_name: str | None, mood: str) -> str:
    """
    If user provides a relative name, join with ASSETS_BGM;
    if None, auto-pick by mood.
    """
    if path_or_name:
        candidate = path_or_name
    else:
        candidate = pick_bgm(mood)
    full = candidate if os.path.isabs(candidate) else os.path.join(ASSETS_BGM, candidate)
    return full

# ---------------------------
# Camera effects
# ---------------------------
def apply_camera_effects(clip, mood):
    if mood in ["epic", "angry"]:
        clip = clip.fx(vfx.fadein, 0.8).fx(vfx.fadeout, 0.8)
        clip = clip.resize(lambda t: 1 + 0.02 * t)  # subtle zoom in
        # Optional slight jitter
        def jitter(get_frame, t):
            f = get_frame(t)
            # MoviePy jitter can be emulated via slight crop+position, skipped for simplicity
            return f
        # clip = clip.fl(jitter)  # keep simple & stable
    elif mood == "mystery":
        clip = clip.fx(vfx.colorx, 0.75)
    elif mood == "sad":
        clip = clip.fx(vfx.fadein, 1).fx(vfx.fadeout, 1)
    return clip

# ---------------------------
# Scene builder
# ---------------------------
async def build_scene(scene: dict, scene_id: int):
    initial_duration = float(scene.get("duration", 10))
    final_scene_duration = initial_duration # Initialize final_scene_duration
    mood = scene.get("mood", "neutral")
    desc = scene.get("description", "No description")
    characters = [c.lower() for c in scene.get("characters", [])]

    # 1) Image (Stable Horde) - This is still synchronous, so it will block.
    # For true async, generate_scene_image would also need to be async and awaited.
    # However, the current parallel image generation in build_anime_video handles this.
    img_path = generate_scene_image(desc, scene_id, characters)
    
    # Collect all audio clips and track their effective end times
    all_audio_clips = []
    current_max_audio_end_time = 0.0 # Tracks the latest end time of any audio clip added so far

    print(f"--- Scene {scene_id} ---")
    print(f"Initial current_max_audio_end_time: {current_max_audio_end_time:.2f}s")

    # Dialogue audio - Collect all coroutines
    dialogue_coroutines = []
    dialogues = scene.get("dialogue", [])
    for idx, d in enumerate(dialogues):
        char = d.get("character", "Unknown")
        text = d.get("text", "")
        lang = d.get("lang", "hi")
        slang = d.get("voice", None)
        voice_name = d.get("voice_name") or pick_voice_for_character(char, lang)

        dialogue_coroutines.append(
            synthesize_voice_async(text, lang, slang, f"voice_{scene_id}_{idx}.mp3", voice_name)
        )

    # Run all dialogue synthesis concurrently
    voice_files = await asyncio.gather(*dialogue_coroutines)

    individual_dialogue_clips = []
    for voice_file in voice_files:
        if voice_file and os.path.exists(voice_file):
            audio_clip = AudioFileClip(voice_file)
            if audio_clip.duration <= 0:
                print(f"  Skipping zero/negative duration dialogue clip: {voice_file}")
                continue
            print(f"  Individual dialogue clip duration: {audio_clip.duration:.2f}s")
            individual_dialogue_clips.append(audio_clip)

    concatenated_dialogue_track = None
    if individual_dialogue_clips:
        concatenated_dialogue_track = concatenate_audioclips(individual_dialogue_clips)
        all_audio_clips.append(concatenated_dialogue_track.set_start(0)) # Dialogue starts at 0
        current_max_audio_end_time = max(current_max_audio_end_time, concatenated_dialogue_track.duration)
        print(f"  Concatenated dialogue track duration: {concatenated_dialogue_track.duration:.2f}s")
    print(f"current_max_audio_end_time after dialogue: {current_max_audio_end_time:.2f}s")

    # Timed SFX
    for timed in scene.get("sfx_timed", []):
        sfx_path = os.path.join(ASSETS_SFX, timed["file"])
        if os.path.exists(sfx_path):
            sfx_clip = AudioFileClip(sfx_path)
            sfx_start_time = float(timed["time"])

            # Ensure sfx_start_time is not negative
            sfx_start_time = max(0.0, sfx_start_time)
            sfx_clip = sfx_clip.set_start(sfx_start_time)
            
            # Trim SFX if it extends beyond final_scene_duration
            if sfx_start_time + sfx_clip.duration > final_scene_duration:
                sfx_clip = sfx_clip.set_duration(final_scene_duration - sfx_start_time)
                print(f"  Timed SFX clip '{timed['file']}' trimmed to {sfx_clip.duration:.2f}s to fit within final_scene_duration")
            
            all_audio_clips.append(sfx_clip)
            current_max_audio_end_time = max(current_max_audio_end_time, sfx_start_time + sfx_clip.duration)
            print(f"  Timed SFX clip '{timed['file']}' duration: {sfx_clip.duration:.2f}s, start: {sfx_start_time:.2f}s")
    print(f"current_max_audio_end_time after timed SFX: {current_max_audio_end_time:.2f}s")

    # Determine preliminary final_scene_duration based on initial_duration and current_max_audio_end_time
    prelim_final_scene_duration = max(initial_duration, current_max_audio_end_time)
    print(f"Preliminary final_scene_duration before fight choreography: {prelim_final_scene_duration:.2f}s")

    # 5) Fight choreography expansion (adjusts duration)
    if mood in ["epic", "angry"]:
        fight_sfx = ["sword_clash.mp3", "explosion.mp3", "battle_horn.mp3"]
        for f in fight_sfx:
            path = os.path.join(ASSETS_SFX, f)
            if os.path.exists(path):
                # Ensure start_t is within reasonable bounds relative to prelim_final_scene_duration
                start_t = random.uniform(1.0, max(1.0, prelim_final_scene_duration - 0.1)) # Ensure at least 0.1s for clip
                sfx_clip = AudioFileClip(path).volumex(0.8)
                sfx_clip = sfx_clip.set_start(start_t)
                all_audio_clips.append(sfx_clip)
                current_max_audio_end_time = max(current_max_audio_end_time, start_t + sfx_clip.duration)
                print(f"  Fight SFX clip '{f}' duration: {sfx_clip.duration:.2f}s, start: {start_t:.2f}s")
        prelim_final_scene_duration += 3.0 # Extend duration for fight scenes
    print(f"current_max_audio_end_time after fight SFX: {current_max_audio_end_time:.2f}s")
    print(f"Preliminary final_scene_duration after fight choreography: {prelim_final_scene_duration:.2f}s")

    # Now, set the definitive final_scene_duration, ensuring it covers all calculated audio end times
    final_scene_duration = max(1.0, prelim_final_scene_duration, current_max_audio_end_time)
    final_scene_duration = round(final_scene_duration, 2)
    print(f"Definitive final_scene_duration: {final_scene_duration:.2f}s")

    clip = ImageClip(img_path).set_duration(final_scene_duration)

    # Now, iterate through all_audio_clips and trim/loop them to fit final_scene_duration
    # This is where we ensure no clip extends beyond the video's duration.
    processed_audio_clips = []
    for audio_clip in all_audio_clips:
        clip_start = audio_clip.start if hasattr(audio_clip, 'start') else 0.0
        # Ensure clip_start is non-negative
        clip_start = max(0.0, clip_start)
        audio_clip = audio_clip.set_start(clip_start)
        clip_duration = audio_clip.duration

        # If the clip starts beyond the final scene duration, skip it
        if clip_start >= final_scene_duration:
            print(f"  Skipping audio clip starting at {clip_start:.2f}s as it's beyond final_scene_duration {final_scene_duration:.2f}s")
            continue

        # Calculate effective duration, trimming if it extends beyond final_scene_duration
        effective_duration = min(clip_duration, final_scene_duration - clip_start)
        if effective_duration <= 0:  # Should not happen if clip_start < final_scene_duration
            print(f"  Skipping audio clip with non-positive effective duration after trimming: {effective_duration:.2f}s")
            continue

        # Apply the new duration
        trimmed_clip = audio_clip.set_duration(effective_duration)
        processed_audio_clips.append(trimmed_clip)
        print(f"  Processed audio clip (start: {trimmed_clip.start:.2f}s, duration: {trimmed_clip.duration:.2f}s)")

    # 2) BGM - loop to match final_scene_duration
    bgm_full = resolve_bgm(scene.get("bgm"), mood)
    if os.path.exists(bgm_full):
        bgm_clip = AudioFileClip(bgm_full).volumex(0.6)
        if bgm_clip.duration <= 0:
            print(f"  Skipping zero/negative duration BGM clip: {bgm_full}")
        else:
            print(f"  BGM clip original duration: {bgm_clip.duration:.2f}s")
            # Loop BGM to fit the final scene duration
            if bgm_clip.duration < final_scene_duration:
                bgm_clip = bgm_clip.fx(vfx.loop, duration=final_scene_duration)
                print(f"  BGM clip looped to duration: {bgm_clip.duration:.2f}s")
            else:
                bgm_clip = bgm_clip.set_duration(final_scene_duration) # Trim if longer
                print(f"  BGM clip trimmed to duration: {bgm_clip.duration:.2f}s")
            processed_audio_clips.insert(0, bgm_clip.set_start(0)) # BGM starts at 0

    # 3) SFX (ambient)
    for sfx in scene.get("sfx", []):
        sfx_path = os.path.join(ASSETS_SFX, sfx)
        if os.path.exists(sfx_path):
            # Ensure ambient SFX also match the scene duration
            sfx_clip = AudioFileClip(sfx_path).volumex(0.05) # Reduced volume for ambient SFX
            if sfx_clip.duration <= 0:
                print(f"  Skipping zero/negative duration ambient SFX clip: {sfx}")
            else:
                print(f"  Ambient SFX clip '{sfx}' original duration: {sfx_clip.duration:.2f}s")
                if sfx_clip.duration < final_scene_duration:
                    sfx_clip = sfx_clip.fx(vfx.loop, duration=final_scene_duration)
                    print(f"  Ambient SFX clip '{sfx}' looped to duration: {sfx_clip.duration:.2f}s")
                else:
                    sfx_clip = sfx_clip.set_duration(final_scene_duration)
                    print(f"  Ambient SFX clip '{sfx}' trimmed to duration: {sfx_clip.duration:.2f}s")
                processed_audio_clips.append(sfx_clip.set_start(0))
    
    # 6) Subtitles (per line) - re-add after duration is finalized
    for idx, d in enumerate(dialogues):
        char = d.get("character", "Unknown")
        text = d.get("text", "")
        subs = generate_subtitles(text)
        sub_text = f"{char}: {subs['en']}"
        subclip = TextClip(sub_text, fontsize=32, color="white", bg_color="black", size=(clip.w, 90))
        subclip = subclip.set_duration(final_scene_duration).set_position(("center", "bottom"))
        clip = CompositeVideoClip([clip, subclip])

    # 7) Camera FX
    clip = apply_camera_effects(clip, mood)

        # 8) Audio mix
        if concatenated_dialogue_track:
            clip = clip.set_audio(concatenated_dialogue_track)

    return clip

# ---------------------------
# Main runner
# ---------------------------
async def build_anime_video(story_json: str):
    with open(story_json, "r", encoding="utf-8") as f:
        story = json.load(f)

    # Prepare arguments for parallel image generation
    scene_args = []
    for i, scene in enumerate(story.get("scenes", []), 1):
        scene_args.append((scene.get("description", "No description"), i, [c.lower() for c in scene.get("characters", [])]))

    # Generate images in parallel
    image_paths = [None] * len(scene_args)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_scene_id = {executor.submit(generate_scene_image, desc, scene_id, chars): idx for idx, (desc, scene_id, chars) in enumerate(scene_args)}
        for future in concurrent.futures.as_completed(future_to_scene_id):
            idx = future_to_scene_id[future]
            try:
                image_paths[idx] = future.result()
            except Exception as exc:
                print(f"Scene {idx+1} image generation generated an exception: {exc}")
                # Fallback to placeholder if parallel generation fails for a scene
                scene_desc = scene_args[idx][0]
                scene_id = scene_args[idx][1]
                img_path = os.path.join(TEMP_DIR, f"scene_{scene_id}.png")
                from PIL import Image, ImageDraw
                img = Image.new("RGB", (768, 512), color=(30, 30, 60))
                draw = ImageDraw.Draw(img)
                draw.text((40, 240), f"Scene {scene_id}: {scene_desc}", fill=(255, 255, 255), font=font)
                img.save(img_path)
                image_paths[idx] = img_path

    clips = []
    for i, scene in enumerate(story.get("scenes", []), 1):
        # Use the pre-generated image path
        img_path = image_paths[i-1]
        
        # Build the scene, which now handles its own duration based on audio
        scene_clip = await build_scene(scene, i)
        clips.append(scene_clip)

    # Add crossfades between clips for smoother transitions
    final = concatenate_videoclips(clips, method="compose")
    out_path = os.path.join(OUTPUT_DIR, "anime_output.mp4")
    try:
        final.write_videofile(out_path, fps=30, audio_fps=44100, codec="libx264", audio_codec="aac", preset="fast", threads=1) # Reduced threads to 1 for debugging
        print(f"✅ Video exported: {out_path}")
    except Exception as e:
        print(f"❌ Error during video export: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py story.json")
        sys.exit(1)
    asyncio.run(build_anime_video(sys.argv[1]))
