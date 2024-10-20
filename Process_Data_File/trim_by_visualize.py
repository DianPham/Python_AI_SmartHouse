import os
import json
import torchaudio
from datasets import Dataset, DatasetDict, Audio
from huggingface_hub import HfApi

# Directories for the train and validation sets
train_audio_dir = "C:/Dian/Data/train_set"  # Directory containing train .wav files
train_vtt_dir = "C:/Dian/Data/train_set" # Directory containing train .vtt files
val_audio_dir = "C:/Dian/Data/validate_set"  # Directory containing validation .wav files
val_vtt_dir = "C:/Dian/Data/validate_set"  # Directory containing validation .vtt files


# Function to read and clean transcript from .vtt file
def read_transcript(vtt_file):
    with open(vtt_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        transcript = ""
        for line in lines:
            if '-->' not in line and line.strip() and "WEBVTT" not in line:  # Remove WEBVTT and empty lines
                transcript += line.strip() + " "
        return transcript.strip()

# Function to load data from audio and matching vtt files
def load_data(audio_dir, vtt_dir):
    data = []
    for audio_file in os.listdir(audio_dir):
        if audio_file.endswith(".wav"):
            audio_path = os.path.join(audio_dir, audio_file)
            # Get the matching VTT file
            vtt_file = os.path.splitext(audio_file)[0] + ".vtt"
            vtt_path = os.path.join(vtt_dir, vtt_file)

            # Load transcript
            if os.path.exists(vtt_path):
                transcript = read_transcript(vtt_path)
                data.append({"audio": audio_path, "text": transcript})
    return data

try:
    # Load train and validation data
    train_data = load_data(train_audio_dir, train_vtt_dir)
    val_data = load_data(val_audio_dir, val_vtt_dir)

    # Convert the data into Hugging Face Dataset format
    train_dataset = Dataset.from_dict({"audio": [example["audio"] for example in train_data], "text": [example["text"] for example in train_data]})
    val_dataset = Dataset.from_dict({"audio": [example["audio"] for example in val_data], "text": [example["text"] for example in val_data]})

    # Set the 'audio' column to load audio files
    train_dataset = train_dataset.cast_column("audio", Audio(sampling_rate=16000))
    val_dataset = val_dataset.cast_column("audio", Audio(sampling_rate=16000))

    # Combine into a DatasetDict
    dataset = DatasetDict({
        "train": train_dataset,
        "validation": val_dataset
    })

    # Push the dataset to Hugging Face Hub
    dataset.push_to_hub("dianpham/datasets_finetuning_PhoWhisper")
except Exception as e:
    print(e)
