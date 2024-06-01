import os
import numpy as np
from pydub import AudioSegment
from scipy.io.wavfile import write

def add_noise(audio_segment, noise_level_db):
    # Convert AudioSegment to numpy array
    samples = np.array(audio_segment.get_array_of_samples()).reshape((-1, audio_segment.channels))
    samples = samples.astype(np.float32)

    # Handle the 0dB case where no noise should be added
    if noise_level_db == 0:
        return audio_segment

    # Generate white noise
    noise = np.random.normal(0, 1, samples.shape)

    # Calculate noise level in linear scale
    noise_level = (noise_level_db / 70)
    
    # Normalize noise to the desired noise level
    noise = noise * noise_level * np.max(np.abs(samples)) / np.max(np.abs(noise))
    
    # Add noise to the original audio
    noisy_samples = samples + noise
    noisy_samples = np.clip(noisy_samples, -32768, 32767).astype(np.int16)
    
    return AudioSegment(
        noisy_samples.tobytes(),
        frame_rate=audio_segment.frame_rate,
        sample_width=audio_segment.sample_width,
        channels=audio_segment.channels
    )

def save_audio(audio_segment, file_name):
    # Save the audio segment using scipy.io.wavfile.write
    samples = np.array(audio_segment.get_array_of_samples()).reshape((-1, audio_segment.channels))
    write(file_name, audio_segment.frame_rate, samples)

def create_noisy_audios(input_dir, output_dir):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Iterate over all files in the directory
    for filename in os.listdir(input_dir):
        if filename.endswith(".wav"):  # Filter files by extension if needed
            filepath = os.path.join(input_dir, filename)
            audio = AudioSegment.from_wav(filepath)
            noise_levels = range(0, 405, 5)

            for noise_level in noise_levels:
                noisy_audio = add_noise(audio, noise_level)
                output_file = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_with_noise_{noise_level}dB.wav")
                save_audio(noisy_audio, output_file)
                print(f"Saved: {output_file}")

# Example usage
input_dir = "C:\\Dian\\SmartHouse\\Test\\WW_audios\\Original"  # Path to your input sample audio file
output_dir = "C:\\Dian\\SmartHouse\\Test\\WW_audios\\Samples"  # Directory to save the noisy audio files

create_noisy_audios(input_dir, output_dir)
