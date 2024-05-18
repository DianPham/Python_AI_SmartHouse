import asyncio
from gtts import gTTS
import pygame
import time
import os

pygame.mixer.init()

async def play_sound(filename):
    pygame.mixer.music.load(filename)
    print(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)  # Non-blocking wait
    pygame.mixer.music.unload()
    os.remove(filename)

def speak(text):
    tts = gTTS(text=text, lang='vi', slow=False)
    filename = f'voice_{int(time.time())}.mp3'
    tts.save(filename)
    asyncio.run(play_sound(filename))