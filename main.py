import os
import subprocess
import requests
import time
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from VoiceAssistant.voice import speak, play_sound
import webrtcvad
import noisereduce as nr

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

def record_audio(filename="audio.wav", duration=10, fs=16000):
    """Record audio from the microphone, stop when silence is detected, and perform noise reduction."""
    print("Start recording...")

    vad = webrtcvad.Vad()
    vad.set_mode(1)  # Level of aggressiveness from 0 to 3

    def callback(indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status)

    # Create a stream object
    stream = sd.InputStream(callback=callback, samplerate=fs, channels=1, dtype='int16')
    start_time = time.time()
    with stream:
        # Initialize variables
        voiced_frames = []
        detected_voice = False

        for _ in range(int(duration * fs / 512)):  # Only loop duration seconds
            data = stream.read(512)[0]  # Read 512 samples
            # Check if the current frame contains speech
            if vad.is_speech(data.tobytes(), sample_rate=fs):
                voiced_frames.append(data)
                detected_voice = True
            elif detected_voice:
                break  # Stop recording after speech stops

    # Convert the list of numpy-arrays into a 1D array (flatten)
    audio_data = np.concatenate(voiced_frames, axis=0)

    # Noise reduction
    reduced_noise_audio = nr.reduce_noise(y=audio_data, sr=fs)

    # Convert to int16 and save as WAV
    write(filename, fs, reduced_noise_audio.astype(np.int16))
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