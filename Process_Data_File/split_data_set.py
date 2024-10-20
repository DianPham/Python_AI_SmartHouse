import os
import random
from shutil import copy2


# Example usage
dir1 = "C:/Dian/Data/vtt"
dir2 = "C:/Dian/Data/norm_audio_2"
output_train = "C:/Dian/Data/train_set"
output_test = "C:/Dian/Data/test_set"

def match_files_by_name(dir1, dir2):
    """
    Match files from two directories based on their names (ignoring extensions).
    
    :param dir1: Path to the first directory
    :param dir2: Path to the second directory
    :return: List of matched file pairs [(file_from_dir1, file_from_dir2), ...]
    """
    # Get the base names (without extension) and map to full paths
    files_dir1 = {os.path.splitext(file)[0]: os.path.join(dir1, file) for file in os.listdir(dir1) if os.path.isfile(os.path.join(dir1, file))}
    files_dir2 = {os.path.splitext(file)[0]: os.path.join(dir2, file) for file in os.listdir(dir2) if os.path.isfile(os.path.join(dir2, file))}

    # Find common base names and create pairs
    matched_files = [(files_dir1[name], files_dir2[name]) for name in files_dir1 if name in files_dir2]

    return matched_files

def separate_data(matched_files, output_train, output_test, train_ratio=0.8):
    # Ensure output directories exist
    os.makedirs(output_train, exist_ok=True)
    os.makedirs(output_test, exist_ok=True)

    # Shuffle the matched files randomly to ensure randomness
    random.shuffle(matched_files)

    # Calculate split index for training and testing
    split_index = int(len(matched_files) * train_ratio)

    # Split the data
    train_files = matched_files[:split_index]
    test_files = matched_files[split_index:]

    # Copy files to the respective train and test directories
    for file1, file2 in train_files:
        copy2(file1, output_train)
        copy2(file2, output_train)
    
    for file1, file2 in test_files:
        copy2(file1, output_test)
        copy2(file2, output_test)

    print(f"Total file pairs: {len(matched_files)}")
    print(f"Training set: {len(train_files)} pairs")
    print(f"Testing set: {len(test_files)} pairs")

# Match files by their names (ignoring file extension)
matched_files = match_files_by_name(dir1, dir2)

separate_data(matched_files, output_train, output_test, train_ratio=0.8)
