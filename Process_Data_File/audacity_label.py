import re

def convert_vtt_to_audacity_label(vtt_file, label_file):
    """
    Converts a VTT file to an Audacity label file format.

    :param vtt_file: Path to the input VTT file
    :param label_file: Path to save the converted Audacity label file
    """
    with open(vtt_file, 'r', encoding='utf-8') as vtt, open(label_file, 'w', encoding='utf-8') as label:
        lines = vtt.readlines()
        for i, line in enumerate(lines):
            # Match time format like: 00:01:02.500 --> 00:01:05.000
            if "-->" in line:
                start_time, end_time = line.split(" --> ")
                start_seconds = convert_time_to_seconds(start_time.strip())
                end_seconds = convert_time_to_seconds(end_time.strip().replace(',', '.'))
                
                # Get the label text from the following lines
                label_text = ""
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() == "" or "-->" in lines[j]:
                        break
                    label_text += lines[j].strip() + " "

                # Write to Audacity label file
                label.write(f"{start_seconds:.3f}\t{end_seconds:.3f}\t{label_text.strip()}\n")

def convert_time_to_seconds(time_str):
    """
    Convert a timestamp from VTT (HH:MM:SS.mmm) format to seconds.

    :param time_str: Time string in HH:MM:SS.mmm format
    :return: Time in seconds (float)
    """
    time_parts = time_str.split(":")
    hours = int(time_parts[0])
    minutes = int(time_parts[1])
    seconds = float(time_parts[2].replace(',', '.'))
    return hours * 3600 + minutes * 60 + seconds

# Example usage
vtt_file = "C:/Dian/Data/merged.vtt"
label_file = "C:/Dian/Data/output_labels.txt"  # Audacity-compatible label file
convert_vtt_to_audacity_label(vtt_file, label_file)
