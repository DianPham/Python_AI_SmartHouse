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

# def record_audio(filename='audio.wav', duration=10, fs=16000, silence_threshold=1, max_silence_duration=5):
#     print("Start Recording..")
#     start_time = time.time()
#     vad = webrtcvad.Vad(2)  # Set mode to 2 for moderate aggressiveness
#     frame_duration = 0.02  # Frame duration in seconds: 20 ms
#     frame_size = int(fs * frame_duration)
#     audio_data = []
    
#     total_silence_duration = 0
#     num_silent_frames = 0
#     silent_frames_threshold = int(silence_threshold / frame_duration)

#     with sd.InputStream(callback=lambda indata, frames, time, status: audio_data.append(indata.copy()) if vad.is_speech(indata[:, 0].tobytes(), fs) else None, samplerate=fs, channels=1, dtype='int16', blocksize=frame_size):
#         while total_silence_duration < max_silence_duration:
#             sd.sleep(int(frame_duration * 1000))  # Sleep for frame duration to reduce CPU usage
#             if not vad.is_speech(audio_data[-1][:, 0].tobytes(), fs):
#                 num_silent_frames += 1
#                 if num_silent_frames >= silent_frames_threshold:
#                     total_silence_duration += num_silent_frames * frame_duration
#                     num_silent_frames = 0
#             else:
#                 num_silent_frames = 0

#     if total_silence_duration >= max_silence_duration:
#         print('Max silence duration reached.')
#         return None

#     print('Recording finished')
#     print("Record in {:.2f} seconds.".format(time.time() - start_time))
#     audio_np = np.concatenate([x.flatten() for x in audio_data], axis=0)

#     try:
#         reduced_noise_audio = nr.reduce_noise(y=audio_np, sr=fs)
#         print('Noise reduction finished.')
#         write(filename, fs, reduced_noise_audio.astype(np.int16))
#         return filename
#     except Exception as e:
#         print(f'Error during noise reduction: {e}')
#         return None
    

# def record_audio(filename='audio.wav', duration=5, fs=16000, silence_threshold=0.2, max_silence_duration=3):
#     print("Start Recording...")
#     vad = webrtcvad.Vad(3)  # Set mode to 2 for moderate aggressiveness
#     frame_duration = 0.02  # Frame duration in seconds: 20 ms
#     frame_size = int(fs * frame_duration)
#     audio_data = []
#     total_silence_duration = 0
#     num_silent_frames = 0
#     silent_frames_threshold = int(silence_threshold / frame_duration)

#     def callback(indata, frames, time, status):
#         nonlocal total_silence_duration, num_silent_frames
#         if status:
#             print("Error:", status)
#         is_speech = vad.is_speech(indata.tobytes(), fs)
#         print("Is speech:", is_speech)

#         if not is_speech:
#             num_silent_frames += 1
#             if num_silent_frames >= 10:
#                 total_silence_duration += num_silent_frames * frame_duration
#                 print("Added silence: " + str(num_silent_frames * frame_duration))
#                 num_silent_frames = 0

#         if total_silence_duration > max_silence_duration:
#             print("Total: " + str(total_silence_duration))
#             print("Max: " + str(max_silence_duration))
#             raise sd.CallbackStop

#         if is_speech:
#             audio_data.append(indata.copy())

#     try:
#         with sd.InputStream(callback=callback, samplerate=fs, channels=1, dtype='int16', blocksize=frame_size) as stream:
#             while True:
#                 time.sleep(0.1)  # This sleep is crucial to not freezing the GUI if any
#     except sd.CallbackStop:
#         print("Silence detected, stopping stream.")
#         if 'stream' in locals():
#             stream.stop()
#             stream.close()
#     except Exception as e:
#         print(f"An error occurred: {e}")

#     if not audio_data:
#         print("No audio data recorded.")
#         return None

#     print('Recording finished.')
#     audio_np = np.concatenate(audio_data, axis=0)

#     try:
#         reduced_noise_audio = nr.reduce_noise(y=audio_np, sr=fs)
#         print('Noise reduction finished.')
#         write(filename, fs, reduced_noise_audio.astype(np.int16))
#         return filename
#     except Exception as e:
#         print(f'Error during noise reduction: {e}')
#         return None


def record_audio(filename='audio.wav', fs=16000, max_silence_duration=0.7):
    print("Start Recording...")
    start_time = time.time()
    vad = webrtcvad.Vad(3)  # Set a moderate aggressiveness mode
    frame_duration = 0.02  # Duration of a frame in seconds
    frame_size = int(fs * frame_duration)
    total_silence_duration = 0
    num_silent_frames = 0
    audio_data = []

    # Initialize the stream
    stream = sd.InputStream(samplerate=fs, channels=1, dtype='int16', blocksize=frame_size)
    try:
        with stream:
            while total_silence_duration < max_silence_duration:
                frame, overflowed = stream.read(frame_size)
                if overflowed:
                    print("Overflow detected in stream.read().")
                
                is_speech = vad.is_speech(frame.tobytes(), fs)
                if is_speech:
                    audio_data.append(frame)  # Reset silence duration
                else:
                    num_silent_frames += 1
                    total_silence_duration = num_silent_frames * frame_duration

                # Append silence if it's within the allowable gap
                if not is_speech and total_silence_duration < max_silence_duration:
                    audio_data.append(frame)

            print("Maximum silence duration reached. Stopping recording.")
    except Exception as e:
        print(f"An error occurred during recording: {e}")

    if not audio_data:
        print("No audio data captured.")
        return None

    # Concatenate all the frames of audio data
    recorded_audio = np.concatenate([x.flatten() for x in audio_data], axis=0)
    print("Record in {:.2f} seconds.".format(time.time() - start_time))

    # Perform noise reduction
    try:
        #reduced_noise_audio = nr.reduce_noise(y=recorded_audio, sr=fs)
        write(filename, fs, recorded_audio)  #reduced_noise_audio.astype(np.int16))  # Save as WAV file
        print(f"Audio recorded and saved to {filename}")
        return filename
    except Exception as e:
        print(f"Error during noise reduction or file writing: {e}")
        return None

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

def in_conversation():
    print("Conversation started")
    play_sound(rising_sound)
    start_time = time.time()
    audio_path = record_audio()  # Record the audio command
    print("Return result in {:.2f} seconds.".format(time.time() - start_time))

    if audio_path is None:
        print("No audio detected or maximum silence reached, going back to sleep.") # Exit if silence is too long or no audio was recorded
        return 
    start_time = time.time()
    speak("Vâng ạ")
    result = send_audio_to_server(audio_path)  # Send the audio to the server and get the transcription
    print("Received result in {:.2f} seconds.".format(time.time() - start_time))
    print("Transcription Result:", result)
    try:   
        response = asyncio.run(get_response(result))
        intent = asyncio.run(get_intent(result))
        print(response)
        print(intent)
        if intent == "end":
            speak(response)
        speak(response)
        print("Received result in {:.2f} seconds.".format(time.time() - start_time))
        #os.remove(audio_path)
    except Exception as e:
        print(f"Failed to send audio to the server: {e}")

def main():
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True  # Set as a daemon so it will be killed once the main program exit   
    if not server_thread.is_alive():
        server_thread.start() 
    if agent is None:
        load_rasa_model()              
    while True:                    
        if detect_wake_word(): # Wait for the wake word to be detected
            speak("Em đây")
            in_conversation()
        time.sleep(1)
        
    
if __name__ == "__main__":
    main()