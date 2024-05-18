import asyncio
import io
import logging
import os
import subprocess
import sys
import threading
import requests
import time
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from VoiceAssistant.voice import speak, play_sound
import webrtcvad
import noisereduce as nr
from rasa.core.agent import Agent
from rasa.core.channels import channel

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

current_dir = os.path.dirname(os.path.realpath(__file__))
path_to_python = os.path.join(current_dir,  "venv\Scripts\python.exe")
path_to_init_server = os.path.join(current_dir, "PhoWhisper_Server\init_server.py")
path_to_activate_ww = os.path.join(current_dir, "WakeWord\ww_interact.py")
rising_sound = "Rising.mp3"
path_to_rasa_model = os.path.join(current_dir, "VoiceAssistant\Rasa\models\demo_model.tar.gz")
agent = None


def start_server():
    """Start the Flask server using a subprocess."""
    # Make sure to specify the correct path to your init_server.py script
    process = subprocess.Popen([path_to_python, path_to_init_server])
    process.wait() 
    
def detect_wake_word():
    process = subprocess.Popen([path_to_python, path_to_activate_ww])
    process.wait()  
    return process.returncode == 0

def record_audio(filename='audio.wav', duration=10, fs=16000, silence_threshold=0.7):
    
    print("Start Recording..")
    start_time = time.time()
    vad = webrtcvad.Vad(2)  # Set mode to 1 for moderate aggressiveness
    frame_duration = 0.02  # Frame duration in seconds: 20 ms
    frame_size = int(fs * frame_duration)
    audio_data = []
    
    def callback(indata, frames, time, status):
        nonlocal num_silent_frames
        if status:
            print("Error:", status)
        if len(indata) < frame_size:
            return  # Skip the incomplete frame
        is_speech = vad.is_speech(indata[:, 0].tobytes(), sample_rate=fs)
        if is_speech:
            num_silent_frames = 0
        else:
            num_silent_frames += 1
        audio_data.append(indata.copy())

    num_silent_frames = 0
    silent_frames_threshold = int(silence_threshold / frame_duration)

    with sd.InputStream(callback=callback, samplerate=fs, channels=1, dtype='int16', blocksize=frame_size):
        while num_silent_frames < silent_frames_threshold:
            sd.sleep(int(frame_duration * 1000))  # Sleep for frame duration to reduce CPU usage

    print('Recording finished')

    # Concatenate all recorded audio frames
    audio_np = np.concatenate([x.flatten() for x in audio_data], axis=0)
    print('Concatenation finished, Data Type:', audio_np.dtype, 'Shape:', audio_np.shape)

    # Noise reduction
    try:
        reduced_noise_audio = nr.reduce_noise(y=audio_np, sr=fs)
        print('Noise reduction finished.')
    except Exception as e:
        print(f'Error during noise reduction: {e}')
        return

    print("Record in {:.2f} seconds.".format(time.time() - start_time))
    # Save the processed audio
    write(filename, fs, reduced_noise_audio.astype(np.int16))
    return filename

def send_audio_to_server(audio_path):
    """Send the audio file to the Flask server for transcription."""
    url = 'http://localhost:5000/transcribe'  # Change this URL to your Flask server's URL
    files = {'file': open(audio_path, 'rb')}
    response = requests.post(url, files=files)
    transcription_result = response.json().get('transcription', {}).get('text', '')
    return transcription_result

def load_rasa_model():
    speak("Tôi đang khởi động lại bạn chờ chút nhé")
    try:
        global agent
        agent = Agent.load(path_to_rasa_model)
        print("Rasa model loaded successfully.")
        return agent
    except Exception as e:
        print(f"Failed to load Rasa model: {e}")
        return None

async def get_response(command):
    try:
        response = await agent.handle_text(command)
        return response[0]["text"]
    except Exception as e:
        print(f"Cannot get response: {e}")
        return None
    
async def get_intent(command):
    try:
        intent = await agent.parse_message(command)
        return intent["intent"]["name"]
    except Exception as e:
        print(f"Cannot get response: {e}")
        return None

def in_conversation(test_command):
    print("Reach function")
    # while True:
    time.sleep(1)
    play_sound(rising_sound)
    #audio_path = record_audio()  # Record the audio command
           
    start_time = time.time()
    #result = send_audio_to_server(audio_path)  # Send the audio to the server and get the transcription
    print("Received result in {:.2f} seconds.".format(time.time() - start_time))
    #print("Transcription Result:", result)
    try:   
        response = asyncio.run(get_response(test_command))
        intent = asyncio.run(get_intent(test_command))
        print(response)
        print(intent)
        if intent == "end":
            speak(response)
            #break
        speak(response)
        #os.remove(audio_path)
    except Exception as e:
        print(f"Failed to send audio to the server: {e}")

def main():
    if agent is None:
        load_rasa_model()          
    # server_thread = threading.Thread(target=start_server)
    # server_thread.daemon = True  # Set as a daemon so it will be killed once the main program exits
    # if not server_thread.is_alive():
    #     speak("Tôi đang khởi động lại bạn chờ chút nhé") 
    #     server_thread.start()              
    # else: 
    if detect_wake_word(): # Wait for the wake word to be detected
        speak("Tôi đây")
        in_conversation("hi")
        
    
if __name__ == "__main__":
    main()