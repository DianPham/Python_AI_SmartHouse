import subprocess

test_data_path = 'C:\\Dian\\SmartHouse\\Test\Rasa\\test_data.json'
model_path = 'C:\\Dian\\SmartHouse\\VoiceAssistant\\Rasa\\models\\demo_model2.tar.gz'
rasa_path = 'C:\\Dian\\SmartHouse\\VoiceAssistant\\Rasa'

command = ['rasa', 'test', 'nlu', '-u', test_data_path, '-m', model_path]

try:
    result = subprocess.run(command, capture_output=True, text=True, env={"SQLALCHEMY_WARN_20": "1"})
    print("Command output:", result.stdout)
except subprocess.CalledProcessError as e:
    print("Error during Rasa testing:", e)
    print(e.stderr)