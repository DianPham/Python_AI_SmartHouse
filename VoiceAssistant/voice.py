import asyncio
from gtts import gTTS
import pygame
import time
import os
import requests
import json
url = "https://viettelai.vn/tts/speech_synthesis"

pygame.mixer.init()

async def play_sound(filename):
    pygame.mixer.music.load(filename)
    print(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)  # Non-blocking wait
    pygame.mixer.music.unload()
    os.remove(filename)

# def speak(text):
#     payload = json.dumps({
#     "text": text,
#     "voice": "hn-thaochi",
#     "speed": 1,
#     "tts_return_option": 2,
#     "token": "$TOKEN",
#     "without_filter": False
#     })
#     tts = gTTS(text=text, lang='vi', slow=False)
#     filename = f'voice_{int(time.time())}.mp3'
#     tts.save(filename)
#     asyncio.run(play_sound(filename))
    
def speak(text):
    payload = json.dumps({
        "text": text,
        "voice": "hn-thaochi",
        "speed": 1,
        "tts_return_option": 2,
        "token": "",
        "without_filter": False
    })
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            filename = f'voice_{int(time.time())}.wav'
            with open(filename, "wb") as file:
                file.write(response.content)
                asyncio.run(play_sound(filename))
        else:
            print(f"Viettel TTS API failed with status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"Error with Viettel TTS API: {e}")
        return None