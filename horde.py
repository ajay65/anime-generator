import requests
import os
import time
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

HORDE_KEY = os.getenv("HORDE_API_KEY", "0000000000") 


# 🛠️ Config
HORDE_API = "https://stablehorde.net/api/v2/generate/async"
HORDE_CHECK = "https://stablehorde.net/api/v2/generate/check"
HORDE_STATUS = "https://stablehorde.net/api/v2/generate/status"
HEADERS = {"apikey": HORDE_KEY}
SAVE_DIR = "generated_images"
os.makedirs(SAVE_DIR, exist_ok=True)

def submit_prompt(prompt: str, width=512, height=512, model="AOM3A3_orangemixs"): #stable_diffusion
    payload = {
        "prompt": prompt,
        "params": {
            "width": width,
            "height": height,
            "n": 1,
            "model": model
        }
    }
    response = requests.post(HORDE_API, json=payload, headers=HEADERS)
    data = response.json()
    print(f"🆔 Request ID: {data['id']} | Kudos used: {data['kudos']}")
    return data['id']

def check_progress(request_id: str):
    response = requests.get(f"{HORDE_CHECK}/{request_id}", headers=HEADERS)
    data = response.json()
    return data.get("finished", 0), data.get("processing", 0)

def get_result(request_id: str):
    response = requests.get(f"{HORDE_STATUS}/{request_id}", headers=HEADERS)
    data = response.json()
    if data.get("done"):
        for i, gen in enumerate(data["generations"]):
            img_url = gen["img"]
            img_data = requests.get(img_url).content
            filename = os.path.join(SAVE_DIR, f"{request_id}_{i}.png")
            with open(filename, "wb") as f:
                f.write(img_data)
            print(f"✅ Saved: {filename}")
            return filename # Return the filename of the generated image
    else:
        print("⏳ Not ready yet.")
    return None # Return None if not ready or no image generated

def generate_image(prompt: str):
    request_id = submit_prompt(prompt)
    while True:
        finished, processing = check_progress(request_id)
        print(f"🔄 Progress — Finished: {finished}, Processing: {processing}")
        if finished > 0:
            break
        time.sleep(5)
    return get_result(request_id)

# 🧪 Example usage
if __name__ == "__main__":
    generate_image("A Japanese high-school rooftop at sunset, cherry blossoms flying in the wind. The Hero and Heroine stand close, silence filled with emotions.")
