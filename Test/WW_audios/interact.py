from collections import defaultdict
import os
import re
import pyaudio
import pvporcupine
import numpy as np
import librosa
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d

def init_porcupine(target_dir):
    """Initialize the Porcupine wake word engine."""
    keyword_path = os.path.join(target_dir, "wakeword_model.ppn")
    model_path = os.path.join(target_dir, "params_vn.pv")
    key = "9+JC9F15GbK8t3XxP295t146coC2gls2/ZaTYemWlufw/MMwXGpSIg=="
    
    porcupine = pvporcupine.create(
        access_key=key, 
        keyword_paths=[keyword_path],
        model_path=model_path, 
        sensitivities=[0.5]  # Sensitivity affects detection likelihood
    )
    return porcupine

def test_wake_word(porcupine, test_dir):
    """Test wake word detection on a set of audio files."""
    results = []
    
    for file_name in os.listdir(test_dir):
        if file_name.endswith(".wav"):
            print("Sending: " + file_name)
            file_path = os.path.join(test_dir, file_name)
            audio, sr = librosa.load(file_path, sr=16000)  # Load and resample to 16 kHz
            audio = audio * 32767  # Scale from [-1, 1] to [-32768, 32767] for int16
            frames = librosa.util.frame(audio, frame_length=porcupine.frame_length, hop_length=porcupine.frame_length)
            
            detected = False
            for frame in frames.T:
                keyword_index = porcupine.process(frame.astype(np.int16))
                if keyword_index >= 0:
                    confidence = 1  # Example confidence (simplistic, as actual confidence isn't provided)
                    results.append((file_name, confidence))
                    detected = True
                    break
            
            if not detected:
                results.append((file_name, 0))  # No detection
            
    return results

def plot_confidence(noise_levels, confidences):
    plt.figure(figsize=(15, 7))
    plt.plot(noise_levels, confidences, linestyle='-', color='blue', linewidth=2, label = 'Accuracy')
    plt.xlabel('Noise Level (dB)')
    plt.ylabel('Average Accuracy')
    plt.title('Average Accuracy by Noise Level')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(range(0, max(noise_levels) + 1, 20))  # Adjust the ticks for better clarity if needed

    # Set the y-axis limits from 0 to 1
    plt.ylim(0, 1.1)
    
    #plt.axhline(y=0.75, color='r', linestyle='--', label='Lowest Accuracy')
    #plt.legend()

    plt.show()

    
def extract_number(filename):
    """ Extracts the number from the filename assuming the format '..._XXXdB.wav' """
    match = re.search(r'(\d+)dB\.wav', filename)
    return int(match.group(1)) if match else 0

if __name__ == "__main__":
    input_dir = "C:\\Dian\\SmartHouse\\Test\\WW_audios\\Samples"
    target_dir = "C:\\Dian\\SmartHouse\\WakeWord"
    pa = pyaudio.PyAudio()
    porcupine = init_porcupine(target_dir)
    
    results = test_wake_word(porcupine, input_dir)
    
    files_with_zero_confidence = []

    # Loop through the results and check the confidence score
    for filename, confidence in results:
        if confidence == 0:
            files_with_zero_confidence.append(filename)

    # Print the filenames with confidence score of 0
    print("Files with a confidence score of 0:")
    for file in files_with_zero_confidence:
        print(file)
    
#    print(sorted(results, key=lambda x: extract_number(x[0])))
    
    confidence_by_level = defaultdict(list)

    for filename, confidence in results:
        noise_level = extract_number(filename)
        if noise_level is not None:
            confidence_by_level[noise_level].append(confidence)
    average_confidence_by_level = {level: sum(confs) / len(confs) for level, confs in confidence_by_level.items()}
    
    noise_levels = sorted(average_confidence_by_level.keys())  # Sorting the noise levels
    confidences = [average_confidence_by_level[level] for level in noise_levels]
    #smoothed_confidences = gaussian_filter1d(confidences, sigma=1)
    #print(noise_levels)
    print(len(results))
    
    # sorted_results = sorted(results, key=lambda x: extract_number(x[0]))
    
    # # Extract noise levels and confidences
    # noise_levels = [int(r[0].split('_')[-1].replace('dB.wav', '')) for r in sorted_results]
    # confidences = [r[1] for r in results]
    
    
    # print(confidences)
    
    plot_confidence(noise_levels, confidences)

    # for file_name, confidence in results:
    #     print(f"File: {file_name}, Confidence: {confidence}")
