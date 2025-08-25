import os
import asyncio
import wave
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydub import AudioSegment
from pydub.utils import which

# ✅ Load API key from .env
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

# ✅ Configure ffmpeg path for pydub
# D:\ajay-dev\projects\anime_generator\ffmpeg-2025-08-20-git-4d7c609be3-essentials_build\bin
# AudioSegment.converter = which("ffmpeg")  # Ensure ffmpeg is installed and in PATH
AudioSegment.converter = r"D:\ajay-dev\projects\anime_generator\ffmpeg-2025-08-20-git-4d7c609be3-essentials_build\bin\ffmpeg.exe"
# ✅ Initialize Gemini client
client = genai.Client(api_key=google_api_key, http_options={'api_version': 'v1alpha'})
anime_bgm_prompts = {
    "happy.mp3": "Anime background music, cheerful, upbeat, light instrumental, fits slice-of-life scenes, inspired by Studio Ghibli happy themes.",
    "sad.mp3": "Emotional anime piano music, slow tempo, soft strings, melancholy and touching atmosphere, inspired by Clannad and Your Lie in April.",
    "romantic.mp3": "Romantic anime BGM with soft piano, acoustic guitar, warm strings, dreamy and heartfelt mood, like a love confession scene.",
    "epic.mp3": "Epic anime battle music with taiko drums, heavy strings, choir, intense orchestration, cinematic like Attack on Titan battle theme.",
    "angry.mp3": "Dark anime BGM with heavy percussion, distorted strings, tense atmosphere, expressing rage and suspense, inspired by Tokyo Ghoul OST.",
    "mystery.mp3": "Mysterious anime soundtrack with eerie pads, light bells, subtle suspense build-up, for mystery or investigation scenes.",
    "neutral.mp3": "Calm and ambient anime background music, light piano and strings, neutral atmosphere for dialogue or transition scenes."
}

anime_sfx_prompts = {
    # "footsteps.mp3": "Realistic anime sound effect of footsteps on solid ground, medium pace walking.",
    # "soft_breeze.mp3": "Soft anime sound effect of wind blowing, gentle ambient breeze in the background.",
    # "sword_clash.mp3": "Anime battle SFX of two swords clashing with metallic impact, sharp and powerful.",
    # "thunder.mp3": "Loud anime thunder sound effect with rumbling reverb, dramatic storm atmosphere.",
    # "explosion.mp3": "Anime action SFX of a huge explosion, deep bass, cinematic impact.",
    # "battle_horn.mp3": "Epic anime war horn sound effect, loud, deep, and dramatic like announcing battle.",
    "fireworks.mp3": "japanese anime style Festive anime fireworks sound effect, multiple bursts, celebratory and bright atmosphere.",
    "river_flow.mp3": "Calm anime sound effect of a flowing river or stream, gentle water movement, peaceful nature ambiance.",
    "birds_chirping.mp3": "Cheerful anime sound effect of birds chirping in a forest, light and melodic bird calls.",
    "city_ambience.mp3": "Lively anime city ambience sound effect, distant traffic, people chatting, urban background noise.",
    "rain.mp3": "Soothing anime rain sound effect, steady rainfall with occasional thunder, relaxing and calming atmosphere.",
    "whisper.mp3": "Soft anime whisper sound effect, gentle and intimate, like a secret being shared.",
    "wind.mp3": "Strong anime wind sound effect, gusty and powerful, conveying a sense of movement and energy.",

}

# 🔁 Combine all prompts
all_prompts = {**anime_bgm_prompts, **anime_sfx_prompts}

# 🎶 Generate and save each track
async def generate_and_save(filename, prompt, duration=10):
    wav_filename = filename.replace(".mp3", ".wav")

    # Prepare WAV file
    wf = wave.open(wav_filename, 'wb')
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(48000)

    async with client.aio.live.music.connect(model='models/lyria-realtime-exp') as session:
        await session.set_weighted_prompts([
            types.WeightedPrompt(text=prompt, weight=1.0)
        ])
        await session.set_music_generation_config(
            config=types.LiveMusicGenerationConfig(bpm=90, temperature=1.0)
        )
        await session.play()
        print(f"🎧 Generating: {filename} — {prompt[:40]}...")

        start_time = time.time()
        try:
            async for message in session.receive():
                if message.server_content.audio_chunks:
                    audio_data = message.server_content.audio_chunks[0].data
                    wf.writeframes(audio_data)

                # Stop after `duration` seconds
                if time.time() - start_time > duration:
                    await session.stop()
                    break
        except asyncio.CancelledError:
            print(f"🛑 Interrupted: {filename}")
        finally:
            wf.close()

    # Convert WAV to MP3
    sound = AudioSegment.from_wav(wav_filename)
    sound.export(filename, format="mp3", bitrate="192k")
    os.remove(wav_filename)
    print(f"✅ Saved: {filename}")

# 🚀 Main runner
async def main():
    for filename, prompt in all_prompts.items():
        await generate_and_save(filename, prompt)

# 🏁 Execute
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⏹️ Interrupted by user.")
