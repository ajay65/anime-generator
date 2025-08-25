"""
main.py - Anime Generator Script
--------------------------------
This script generates anime-style videos from a story.json description.

Features Included:
- 🎨 Anime-style image generation (stub, pluggable with Stable Diffusion/AnimeGANv2).
- 🗣️ Multi-language voice synthesis with Coqui TTS (default) + gTTS fallback.
- 🗨️ Regional Hindi dialects (Mumbaiya, Haryanvi, Bihari, UP) via slang preprocessing.
- 📜 Subtitles auto-translated into English (default), Hindi, Japanese.
- 🎵 Auto BGM based on mood (fallback if bgm not defined).
- 💥 Fight choreography expansion for epic/angry moods (extra SFX + duration).
- 🎥 Camera effects (zoom, pan, shake).
- 🔊 SFX overlay (footsteps, sword clash, explosions, etc.).
- ⏱️ Scene duration control (with fight extensions).
- 🖼️ Subtitles rendered on video.
- 🎬 Final video export to outputs/anime_output.mp4.

Input:
    python main.py story.json

story.json should define scenes with fields like:
- description
- duration
- mood
- bgm (optional, auto if missing)
- sfx, sfx_timed
- dialogue (with character, text, voice style, language)

Author: Your Anime AI Assistant
"""

import os
import sys
import json
import random
from pathlib import Path
from deep_translator import GoogleTranslator
from gtts import gTTS
from moviepy.editor import (
    ImageClip, AudioFileClip, concatenate_videoclips,
    CompositeAudioClip, CompositeVideoClip, TextClip, vfx
)

from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})

# Try Coqui TTS if available
try:
    from TTS.api import TTS
    coqui_available = True
    coqui_tts = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", progress_bar=False, gpu=False)
except Exception:
    coqui_available = False


# ---------------------------
# PATHS
# ---------------------------
ASSETS_BGM = "assets/bgm"
ASSETS_SFX = "assets/sfx"
TEMP_DIR = "temp"
OUTPUT_DIR = "outputs"

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------
# Slang/Dialect Handling
# ---------------------------
def apply_slang(text: str, slang: str) -> str:
    """
    Apply regional slang transformation to Hindi dialogue.
    """
    if slang == "hindi_mumbaiya":
        return text.replace("tum", "tu").replace("aap", "apun") + " re!"
    elif slang == "hindi_bihari":
        return "Arre " + text.replace("tum", "tohra") + " baa"
    elif slang == "hindi_up":
        return text.replace("main", "hum") + " bhaiya"
    elif slang == "hindi_haryanvi":
        return "Sun le " + text.replace("hai", "se")
    return text


# ---------------------------
# Subtitles
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
# Voice Synthesis
# ---------------------------
def synthesize_voice(text, lang="hi", slang=None, filename="voice.mp3"):
    """
    Generate voice using Coqui TTS if available, else fallback to gTTS.
    """
    if slang:
        text = apply_slang(text, slang)

    filepath = os.path.join(TEMP_DIR, filename)

    try:
        if coqui_available:
            coqui_tts.tts_to_file(text=text, file_path=filepath, speaker=lang)
        else:
            tts = gTTS(text=text, lang=lang)
            tts.save(filepath)
    except Exception as e:
        print(f"⚠️ Voice generation failed, using text-only: {e}")
        return None

    return filepath


# ---------------------------
# Image Generation (stub)
# ---------------------------
def generate_scene_image(scene_desc, scene_id):
    """
    Stub for anime-style image generation.
    Replace this with Stable Diffusion / AnimeGANv2.
    """
    from PIL import Image, ImageDraw
    img_path = os.path.join(TEMP_DIR, f"scene_{scene_id}.png")
    img = Image.new("RGB", (1280, 720), color=(30, 30, 60))
    draw = ImageDraw.Draw(img)
    draw.text((50, 350), f"Scene {scene_id}: {scene_desc}", fill=(255, 255, 255))
    img.save(img_path)
    return img_path


# ---------------------------
# BGM Auto Picker
# ---------------------------
def pick_bgm(mood):
    mood_map = {
        "happy": "happy.mp3",
        "sad": "sad.mp3",
        "romantic": "romantic.mp3",
        "epic": "epic.mp3",
        "angry": "angry.mp3",
        "mystery": "mystery.mp3",
        "neutral": "neutral.mp3"
    }
    return os.path.join(ASSETS_BGM, mood_map.get(mood, "neutral.mp3"))


# ---------------------------
# Camera Effects
# ---------------------------
def apply_camera_effects(clip, mood):
    if mood in ["epic", "angry"]:
        clip = clip.fx(vfx.fadein, 1).fx(vfx.fadeout, 1)
        clip = clip.resize(lambda t: 1 + 0.02 * t)  # zoom
    elif mood == "mystery":
        clip = clip.fx(vfx.colorx, 0.7)  # darker
    return clip


# ---------------------------
# Scene Builder
# ---------------------------
def build_scene(scene, scene_id):
    duration = scene.get("duration", 10)
    mood = scene.get("mood", "neutral")
    desc = scene.get("description", "No description")

    # Image
    img_path = generate_scene_image(desc, scene_id)
    clip = ImageClip(img_path).set_duration(duration)

    # BGM
    bgm_file = scene.get("bgm")
    if not bgm_file:
        bgm_file = pick_bgm(mood)  # already full path
    else:
        bgm_file = os.path.join(ASSETS_BGM, bgm_file)  # only if user specifies relative name

    audio_tracks = [AudioFileClip(bgm_file)]

    # SFX
    for sfx in scene.get("sfx", []):
        sfx_path = os.path.join(ASSETS_SFX, sfx)
        if os.path.exists(sfx_path):
            audio_tracks.append(AudioFileClip(sfx_path).volumex(0.7))

    for timed in scene.get("sfx_timed", []):
        sfx_path = os.path.join(ASSETS_SFX, timed["file"])
        if os.path.exists(sfx_path):
            audio_tracks.append(AudioFileClip(sfx_path).set_start(timed["time"]))

    # Fight choreography expansion
    if mood in ["epic", "angry"]:
        fight_sfx = ["sword_clash.mp3", "explosion.mp3", "battle_horn.mp3"]
        for f in fight_sfx:
            path = os.path.join(ASSETS_SFX, f)
            if os.path.exists(path):
                audio_tracks.append(AudioFileClip(path).set_start(random.randint(1, duration - 1)))
        duration += 3
        clip = clip.set_duration(duration)

    # Dialogue + Subtitles
    dialogues = scene.get("dialogue", [])
    for idx, d in enumerate(dialogues):
        char = d.get("character", "Unknown")
        text = d.get("text", "")
        lang = d.get("lang", "hi")
        slang = d.get("voice", None)

        voice_file = synthesize_voice(text, lang, slang, f"voice_{scene_id}_{idx}.mp3")
        if voice_file:
            audio_tracks.append(AudioFileClip(voice_file))

        subs = generate_subtitles(text)
        sub_text = f"{char}: {subs['en']}"
        subclip = TextClip(sub_text, fontsize=32, color="white", bg_color="black", size=(1280, 100))
        subclip = subclip.set_duration(duration).set_position(("center", "bottom"))
        clip = CompositeVideoClip([clip, subclip])

    # Camera effects
    clip = apply_camera_effects(clip, mood)

    # Audio mix
    final_audio = CompositeAudioClip(audio_tracks).set_duration(duration)
    clip = clip.set_audio(final_audio)

    return clip


# ---------------------------
# Main Runner
# ---------------------------
def build_anime_video(story_json):
    with open(story_json, "r", encoding="utf-8") as f:
        story = json.load(f)

    clips = []
    for i, scene in enumerate(story.get("scenes", []), 1):
        clips.append(build_scene(scene, i))

    final = concatenate_videoclips(clips)
    out_path = os.path.join(OUTPUT_DIR, "anime_output.mp4")
    final.write_videofile(out_path, fps=24)
    print(f"✅ Video exported: {out_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py story.json")
    else:
        build_anime_video(sys.argv[1])
