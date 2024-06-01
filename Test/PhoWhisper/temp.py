import os


for filename in os.listdir("C:\\Dian\\SmartHouse\\Test\\PhoWhisper\\test_set\\transcripts"):
    transcript_path = os.path.join("C:\\Dian\\SmartHouse\\Test\\PhoWhisper\\test_set\\transcripts", os.path.splitext(filename)[0] + '.txt')
    with open(transcript_path, 'a', encoding='utf-8') as file:
        file.write(".")