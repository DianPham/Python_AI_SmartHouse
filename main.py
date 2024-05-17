import os
import subprocess
import requests
import time
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from VoiceAssistant.voice import speak, play_sound

path_to_python = "C:/Dian/SmartHouse#2/venv/Scripts/python.exe"
path_to_init_server = "C:/Dian/SmartHouse#2/PhoWhisper_Server/init_server.py"
path_to_activate_ww = "C:/Dian/SmartHouse#2/WakeWord/ww_interact.py"
rising_sound = "Rising.mp3"

def start_server():
    """Start the Flask server using a subprocess."""
    # Make sure to specify the correct path to your init_server.py script
    subprocess.Popen([path_to_python, path_to_init_server])

def detect_wake_word():
    process = subprocess.Popen([path_to_python, path_to_activate_ww])
    process.wait()  
    return process.returncode == 1

def record_audio(filename="audio.wav", duration=2, fs=16000):
    """Record audio from the microphone and save it as a WAV file."""
    print("Start recording...")
    start_time = time.time()
    audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait()  # Wait until recording is finished
    write(filename, fs, (audio_data * 32767).astype(np.int16))  # Convert to int16 and save as WAV
    print("Finish recording. Saved as", filename, "in {:.2f} seconds.".format(time.time() - start_time))
    return filename

def send_audio_to_server(audio_path):
    """Send the audio file to the Flask server for transcription."""
    url = 'http://localhost:5000/transcribe'  # Change this URL to your Flask server's URL
    files = {'file': open(audio_path, 'rb')}
    response = requests.post(url, files=files)
    transcription_result = response.json().get('transcription', {}).get('text', '')
    return transcription_result

if __name__ == "__main__":
    #start_server() 
    if detect_wake_word(): # Wait for the wake word to be detected
        speak("Tôi đây")
        play_sound(rising_sound)
        audio_path = record_audio(duration=3)  # Record the audio command
        try:
            start_time = time.time()
            result = send_audio_to_server(audio_path)  # Send the audio to the server and get the transcription
            print("Received result in {:.2f} seconds.".format(time.time() - start_time))
            print("Transcription Result:", result)
            os.remove(audio_path)
        except Exception as e:
            print(f"Failed to send audio to the server: {e}")