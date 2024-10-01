import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import struct
import sys
import pyaudio
import pvporcupine

def create_audio_stream(pa):
    """Create an audio stream with PyAudio."""
    audio_stream = pa.open(
        rate=16000,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=512
    )
    return audio_stream



def init_porcupine(current_dir):
    """Initialize the Porcupine wake word engine."""
    keyword_path = os.path.join(current_dir, "wakeword_model.ppn")
    model_path = os.path.join(current_dir, "params_vn.pv")
    key = "LWnH1h7LDEgAu+7Ec8g7tMT1ClbgFv/HbLCFcQyXn0f/v+bvMve9aQ=="
    
    porcupine = pvporcupine.create(
        access_key=key, 
        keyword_paths=[keyword_path],
        model_path=model_path, 
        sensitivities=[0.5]
    )
    return porcupine

def get_next_audio_frame(audio_stream, frame_length):
    """Get the next block of audio frames."""
    audio_frame = audio_stream.read(512, exception_on_overflow=False)
    pcm = struct.unpack_from("h" * frame_length, audio_frame)
    return pcm

def activate_ww(porcupine, audio_stream):
    """Activate wake word detection."""
    try:
        print("[Yumi] Sleeping...zZ")
        while True:
            pcm = get_next_audio_frame(audio_stream, porcupine.frame_length)
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print(pcm)
                sys.exit(0)
    except KeyboardInterrupt:
        print("Stopping")
    finally:
        porcupine.delete()
        audio_stream.close()
        pa.terminate()

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.realpath(__file__))
    pa = pyaudio.PyAudio()
    porcupine = init_porcupine(current_dir)
    audio_stream = create_audio_stream(pa)
    
    activate_ww(porcupine, audio_stream)
